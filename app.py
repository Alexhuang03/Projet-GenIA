"""
Interface Streamlit · Assistant Aides Étudiantes & CROUS
Niveau 0 (LLM seul) et Niveau 1 (RAG avec sources citées et abstention), comparables côte à côte.
Mineur IA Générative 2026 · Dr. Issam Falih
"""
import os

import streamlit as st

from src.baseline.level0_llm import Level0LLM, SYSTEM_PROMPT_LEVEL_0
from src.llm_client import UnifiedLLMClient
from src.rag.engine import RAGEngine, SYSTEM_PROMPT_RAG
from src.rag.retriever import Retriever

st.set_page_config(page_title="Assistant Aides Étudiantes", page_icon="🎓", layout="wide")


@st.cache_resource
def get_client(provider: str, model: str) -> UnifiedLLMClient:
    return UnifiedLLMClient(provider=provider, model=model or None)


@st.cache_resource
def get_retriever(provider: str, model: str, mode: str) -> Retriever:
    return Retriever(get_client(provider, model), mode=mode)


for key, default in (("messages", []), ("session_tokens", 0), ("session_latencies", [])):
    st.session_state.setdefault(key, default)

# --- Barre latérale ------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Paramètres")
    st.info("**Progression :**\n- 🟢 Niveau 0 : LLM seul (S1)\n- 🟢 Niveau 1 : RAG (S2)\n"
            "- ⏳ Niveau 2 : Agent (S3)\n- ⏳ Niveau 3 : Extension (S4)")

    level = st.radio("Niveau", [1, 0], format_func=lambda x: {0: "0 · LLM seul", 1: "1 · RAG"}[x])
    retriever_mode = st.selectbox("Recherche (Niveau 1)", ["hybrid", "bm25", "dense"],
                                  disabled=level == 0)

    st.markdown("---")
    st.subheader("🔌 Fournisseur LLM")
    provider = st.selectbox("Fournisseur", ["ollama", "groq", "gemini", "openai", "mock"],
                            help="mock = réponses factices, pour tester l'interface sans modèle")
    model = st.text_input("Modèle (vide = défaut)", value="")
    if provider in ("groq", "gemini", "openai"):
        key = st.text_input(f"Clé API {provider}", type="password", help="Optionnel si définie dans .env")
        if key:
            os.environ[f"{provider.upper()}_API_KEY"] = key

    st.markdown("---")
    st.subheader("📊 Session")
    c1, c2 = st.columns(2)
    c1.metric("Tokens cumulés", st.session_state.session_tokens)
    lats = st.session_state.session_latencies
    c2.metric("Latence moy.", f"{(sum(lats) / len(lats)) if lats else 0:.2f}s")
    if st.button("🗑️ Réinitialiser"):
        st.session_state.messages, st.session_state.session_tokens, st.session_state.session_latencies = [], 0, []
        st.rerun()

client = get_client(provider, model)

# --- Zone centrale -------------------------------------------------------------
st.header("🎓 Assistant Aides Étudiantes & CROUS")
st.caption(f"Niveau {level} · LLM `{client.provider}:{client.model}`"
           + (f" · recherche `{retriever_mode}`" if level == 1 else ""))
if client.is_mock:
    st.warning("Mode mock : aucune vraie génération, réponses factices.")

with st.expander("📜 Prompt système du niveau sélectionné"):
    st.code(SYSTEM_PROMPT_RAG if level == 1 else SYSTEM_PROMPT_LEVEL_0, language="text")

st.markdown("**Exemples :**")
examples = [
    ("Montant de l'échelon 0bis", "Quel est le montant annuel de l'échelon 0bis de la bourse CROUS ?"),
    ("Visale : combien de mois ?", "Combien de mensualités d'impayés de loyer la garantie Visale peut-elle couvrir au maximum ?"),
    ("Hors corpus (voilier)", "Quelle est la subvention du CROUS pour l'achat d'un voilier ou yacht de plaisance étudiant ?"),
]
for col, (label, q) in zip(st.columns(len(examples)), examples):
    if col.button(label):
        st.session_state.sample_query = q


def render_meta(m: dict):
    with st.expander("🔍 Sources, passages et trace"):
        cols = st.columns(3)
        cols[0].metric("Latence", f"{m['latency']:.2f}s")
        cols[1].metric("Tokens", m["tokens"])
        cols[2].metric("Statut", m["status"])
        if m.get("chunks"):
            st.markdown("**Passages récupérés :**")
            for ch in m["chunks"]:
                st.markdown(f"`#{ch['rank']}` **{ch['doc']}** · {ch['section']} (score {ch['score']:.3f})")
                st.caption(ch["content"][:400])
        if m.get("citations_invalides"):
            st.error(f"Sources citées mais non fournies : {m['citations_invalides']}")
        st.json(m["steps"])


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            render_meta(msg["meta"])

query = st.chat_input("Posez votre question...")
if st.session_state.get("sample_query"):
    query, st.session_state.sample_query = st.session_state.sample_query, None

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner(f"Niveau {level} en cours..."):
            try:
                if level == 1:
                    result = RAGEngine(client, get_retriever(provider, model, retriever_mode)).process(query)
                else:
                    result = Level0LLM(client).process(query)
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()
        tr = result["trace"]
        meta = {"latency": tr["latency_seconds"], "tokens": tr["total_tokens"], "status": tr["status"],
                "steps": tr["steps"], "chunks": result.get("retrieved_chunks"),
                "citations_invalides": result.get("citations_invalides")}
        st.session_state.session_tokens += meta["tokens"]
        st.session_state.session_latencies.append(meta["latency"])
        st.session_state.messages.append({"role": "assistant", "content": result["response"], "meta": meta})
        st.rerun()
