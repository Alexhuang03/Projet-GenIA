"""
Interface Streamlit · Assistant Aides Étudiantes & CROUS
Les 4 niveaux sur la même demande : 0 LLM seul, 1 RAG, 2 agent ReAct, 3 agent ReWOO (extension).
Affiche la réponse, les sources, la trace (étapes, outils, arguments, tokens, durée) et demande
la confirmation de l'étudiant avant toute action irréversible.
Mineur IA Générative 2026 · Dr. Issam Falih
"""
import os

import streamlit as st

from src.agent.common import AGENT_RULES
from src.agent.loop import ReActAgent
from src.agent.rewoo import ReWOOAgent
from src.agent.tools import TOOL_SPECS
from src.baseline.level0_llm import Level0LLM, SYSTEM_PROMPT_LEVEL_0
from src.llm_client import UnifiedLLMClient
from src.rag.engine import RAGEngine, SYSTEM_PROMPT_RAG
from src.rag.retriever import Retriever

st.set_page_config(page_title="Assistant Aides Étudiantes", page_icon="🎓", layout="wide")
LEVELS = {0: "0 · LLM seul", 1: "1 · RAG", 2: "2 · Agent (ReAct)", 3: "3 · Agent planificateur (ReWOO)"}


@st.cache_resource
def get_client(provider: str, model: str) -> UnifiedLLMClient:
    return UnifiedLLMClient(provider=provider, model=model or None)


@st.cache_resource
def get_retriever(provider: str, model: str, mode: str) -> Retriever:
    return Retriever(get_client(provider, model), mode=mode)


def md_table(rows: list) -> None:
    """Tableau en Markdown (st.table dépend de pyarrow, indisponible sur certaines versions de Python)."""
    clean = lambda v: " ".join(str(v).split()).replace("|", "/")
    head = list(rows[0])
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(clean(r[h]) for h in head) + " |" for r in rows]
    st.markdown(chr(10).join(lines))


for key, default in (("messages", []), ("session_tokens", 0), ("session_latencies", []), ("pending", None)):
    st.session_state.setdefault(key, default)

# --- Barre latérale ------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Paramètres")
    level = st.radio("Niveau", [3, 2, 1, 0], format_func=LEVELS.get)
    retriever_mode = st.selectbox("Recherche documentaire", ["hybrid", "bm25", "dense"], disabled=level == 0)

    st.markdown("---")
    st.subheader("🔌 Fournisseur LLM")
    provider = st.selectbox("Fournisseur", ["ollama", "groq", "gemini", "openai", "mock"],
                            help="Niveaux 2 et 3 : Ollama (appel d'outils natif). mock = réponses factices.")
    model = st.text_input("Modèle (vide = défaut)", value="")
    if provider in ("groq", "gemini", "openai"):
        key = st.text_input(f"Clé API {provider}", type="password", help="Optionnel si définie dans .env")
        if key:
            os.environ[f"{provider.upper()}_API_KEY"] = key

    st.markdown("---")
    st.subheader("📊 Coûts de la session")
    c1, c2 = st.columns(2)
    c1.metric("Tokens cumulés", st.session_state.session_tokens)
    lats = st.session_state.session_latencies
    c2.metric("Latence moy.", f"{(sum(lats) / len(lats)) if lats else 0:.2f}s")
    if st.button("🗑️ Réinitialiser"):
        for k in ("messages", "session_latencies"):
            st.session_state[k] = []
        st.session_state.session_tokens, st.session_state.pending = 0, None
        st.rerun()

client = get_client(provider, model)


def build_system(lvl: int):
    if lvl == 0:
        return Level0LLM(client)
    retriever = get_retriever(provider, model, retriever_mode)
    return {1: RAGEngine, 2: ReActAgent, 3: ReWOOAgent}[lvl](client, retriever)


# --- Zone centrale -------------------------------------------------------------
st.header("🎓 Assistant Aides Étudiantes & CROUS")
st.caption(f"Niveau {LEVELS[level]} · LLM `{client.provider}:{client.model}`"
           + (f" · recherche `{retriever_mode}`" if level else ""))
if client.is_mock:
    st.warning("Mode mock : aucune vraie génération, réponses factices.")
if level >= 2 and provider != "ollama":
    st.error("Les niveaux 2 et 3 utilisent l'appel d'outils natif d'Ollama : choisissez le fournisseur ollama.")

with st.expander("📜 Prompt système et outils du niveau sélectionné"):
    st.code({0: SYSTEM_PROMPT_LEVEL_0, 1: SYSTEM_PROMPT_RAG}.get(level, AGENT_RULES), language="text")
    if level >= 2:
        md_table([{"outil": n, "effet": s["effect"], "description": s["schema"]["function"]["description"][:110]}
                  for n, s in TOOL_SPECS.items()])

st.markdown("**Exemples :**")
examples = [
    ("Question documentaire", "Quel est le montant annuel de l'échelon 0bis de la bourse CROUS ?"),
    ("Hors corpus (voilier)", "Quelle est la subvention du CROUS pour l'achat d'un voilier ou yacht de plaisance étudiant ?"),
    ("Tâche + enregistrement", "Mon université est à 260 km de chez mes parents. J'ai 2 frères dans le supérieur. "
                               "Calcule mes points de charge, estime mon échelon pour un revenu fiscal de 12 000 euros "
                               "et génère mon dossier de simulation."),
]
for col, (label, q) in zip(st.columns(len(examples)), examples):
    if col.button(label, disabled=st.session_state.pending is not None):
        st.session_state.sample_query = q


def render_meta(m: dict):
    with st.expander("🔍 Trace : étapes, outils, sources, coûts"):
        cols = st.columns(4)
        cols[0].metric("Latence", f"{m['latency']:.2f}s")
        cols[1].metric("Tokens", m["tokens"])
        cols[2].metric("Appels LLM", m.get("llm_calls", 1))
        cols[3].metric("Statut", m["status"])
        if m.get("tool_log"):
            st.markdown("**Appels d'outils :**")
            md_table([{"outil": e["tool"], "effet": e.get("effect"), "arguments": str(e["arguments"])[:120],
                       "résultat": "✅" if e.get("ok") else f"❌ {e.get('error', '')[:80]}",
                       "durée": f"{e.get('duree_s', 0):.2f}s"} for e in m["tool_log"]])
        if m.get("chunks"):
            st.markdown("**Passages récupérés :**")
            for ch in m["chunks"]:
                st.markdown(f"`#{ch['rank']}` **{ch['doc']}** · {ch.get('section', '')}")
                st.caption(ch["content"][:300])
        if m.get("citations_invalides"):
            st.error(f"Sources citées mais non fournies : {m['citations_invalides']}")
        st.json(m["steps"], expanded=False)


def record(result: dict, lvl: int):
    tr = result["trace"]
    meta = {"latency": tr["latency_seconds"], "tokens": tr["total_tokens"], "status": tr["status"],
            "steps": tr["steps"], "chunks": result.get("retrieved_chunks"), "llm_calls": result.get("llm_calls", 1),
            "tool_log": result.get("tool_log"), "citations_invalides": result.get("citations_invalides")}
    st.session_state.session_tokens += meta["tokens"]
    st.session_state.session_latencies.append(meta["latency"])
    st.session_state.messages.append({"role": "assistant", "content": result["response"], "meta": meta})
    if result.get("status") == "WAITING_CONFIRMATION":
        st.session_state.pending = {"level": lvl, "session": result["session"]}
    else:
        st.session_state.pending = None


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            render_meta(msg["meta"])

# --- Confirmation d'une action irréversible ------------------------------------
pending = st.session_state.pending
if pending:
    st.warning("L'agent attend votre décision avant d'exécuter l'action irréversible ci-dessus.")
    c_yes, c_no = st.columns(2)
    decision = True if c_yes.button("✅ Confirmer l'action", type="primary") else (
        False if c_no.button("❌ Refuser") else None)
    if decision is not None:
        st.session_state.messages.append({"role": "user", "content": "✅ Je confirme." if decision else "❌ Je refuse."})
        with st.spinner("Reprise de l'agent..."):
            result = build_system(pending["level"]).resume(pending["session"], decision)
        record(result, pending["level"])
        st.rerun()

query = st.chat_input("Posez votre question...", disabled=pending is not None)
if st.session_state.get("sample_query"):
    query, st.session_state.sample_query = st.session_state.sample_query, None

if query and not pending:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner(f"Niveau {LEVELS[level]} en cours..."):
            try:
                result = build_system(level).process(query)
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()
    record(result, level)
    st.rerun()
