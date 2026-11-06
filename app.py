"""
Interface Interactive Streamlit - Assistant IA Générative pour les Aides Étudiantes
Conforme au cahier des charges du Dr. Issam Falih :
- Choix dynamique du niveau (0 : LLM seul, 1 : RAG, 2 : Agent outillé)
- Affichage des réponses, des sources citées et des coûts (tokens, latence)
- Traces complètes d'exécution et validation interactive des actions irréversibles
"""
import streamlit as st
import time
import json
from pathlib import Path

from src.config import CORPUS_DIR, TRACES_PATH, EXPORTS_DIR
from src.llm_client import UnifiedLLMClient
from src.baseline.level0_llm import Level0LLM
from src.rag.retriever import HybridRetriever
from src.rag.engine import RAGEngine
from src.agent.loop import AgentLoop

st.set_page_config(
    page_title="Assistant Aides Étudiantes - IA Générative",
    page_icon="🎓",
    layout="wide"
)

# Initialisation du cache des modules pour la réactivité
@st.cache_resource
def get_retriever():
    return HybridRetriever()

@st.cache_resource
def get_llm_client(provider: str, api_key: str):
    import os
    if api_key:
        if provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
    return UnifiedLLMClient(provider=provider)

# Initialisation de l'état de session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "session_tokens" not in st.session_state:
    st.session_state.session_tokens = 0
if "session_latencies" not in st.session_state:
    st.session_state.session_latencies = []

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Paramètres & Niveaux")
    
    level_choice = st.radio(
        "Niveau du système :",
        options=[0, 1, 2],
        format_func=lambda x: {
            0: "0 · LLM seul (Baseline à battre)",
            1: "1 · RAG (Recherche + Citations + Abstention)",
            2: "2 · Agent outillé (ReAct pur Python + Actions)"
        }[x],
        index=2
    )

    st.markdown("---")
    st.subheader("🔌 Modèle & Fournisseur")
    provider_choice = st.selectbox(
        "Fournisseur LLM :",
        ["mock", "gemini", "groq", "openai"],
        format_func=lambda x: {
            "mock": "Mode Démo / Hors-ligne (Instant)",
            "gemini": "Google Gemini (gemini-2.5-flash)",
            "groq": "Groq Cloud (Llama 3.3)",
            "openai": "OpenAI (GPT-4o-mini)"
        }[x]
    )

    custom_key = ""
    if provider_choice != "mock":
        custom_key = st.text_input(
            f"Clé API {provider_choice.capitalize()} (optionnel) :",
            type="password",
            help="Laissez vide pour utiliser la variable d'environnement ou le mock."
        )

    st.markdown("---")
    st.subheader("📊 Métriques de session")
    col_t, col_l = st.columns(2)
    with col_t:
        st.metric("Tokens cumulés", f"{st.session_state.session_tokens}")
    with col_l:
        avg_lat = (
            sum(st.session_state.session_latencies) / len(st.session_state.session_latencies)
            if st.session_state.session_latencies else 0.0
        )
        st.metric("Latence moy.", f"{avg_lat:.2f}s")

    st.markdown("---")
    if st.button("🗑️ Réinitialiser la conversation"):
        st.session_state.messages = []
        st.session_state.pending_action = None
        st.session_state.session_tokens = 0
        st.session_state.session_latencies = []
        st.rerun()

# Instanciation des composants
client = get_llm_client(provider_choice, custom_key)
retriever = get_retriever()
level0_model = Level0LLM(client)
rag_engine = RAGEngine(client, retriever)
agent_engine = AgentLoop(client)

# --- ZONE CENTRALE ---
st.header("🎓 Assistant Aides Étudiantes & CROUS")
st.caption("Système génératif qui se mesure · Mineur IA Générative 2026 · Dr. Issam Falih")

# Bandeau explicatif du niveau actif
if level_choice == 0:
    st.info("ℹ️ **Niveau 0 (LLM seul)** : Aucune base documentaire, aucun outil. Prompt soigné servant de baseline de référence à battre.")
elif level_choice == 1:
    st.info("ℹ️ **Niveau 1 (RAG)** : Indexation hybride (Dense + BM25). Citations explicites des sources et **abstention** si le corpus ne contient pas la réponse.")
elif level_choice == 2:
    st.info("ℹ️ **Niveau 2 (Agent outillé)** : Boucle ReAct écrite **sans framework**, respect des barèmes vérifié par code, validation humaine exigée pour les actions irréversibles.")

# Exemples rapides de requêtes
st.markdown("**Suggestions de test :**")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📄 RAG : Montant échelon 0bis"):
        st.session_state.sample_query = "Quel est le montant annuel de l'échelon 0bis de la bourse CROUS ?"
with col2:
    if st.button("🚫 Abstention : Subvention voilier"):
        st.session_state.sample_query = "Quelle est la subvention du CROUS pour l'achat d'un voilier ou yacht de plaisance ?"
with col3:
    if st.button("🤖 Agent : Calcul de points & Sauvegarde"):
        st.session_state.sample_query = "Je suis à 310 km de ma fac, j'ai 1 frère à la fac et 1 sœur au collège. Calcule mes points et sauvegarde mon dossier."

# Affichage des messages précédents
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg and msg["meta"]:
            m = msg["meta"]
            with st.expander("🔍 Observabilité & Traces de la requête"):
                cols = st.columns(4)
                cols[0].metric("Niveau", m.get("level", 0))
                cols[1].metric("Latence", f"{m.get('latency', 0.0):.3f}s")
                cols[2].metric("Tokens", m.get("tokens", 0))
                cols[3].metric("Statut", m.get("status", "N/A"))
                
                if m.get("sources"):
                    st.markdown("**📚 Sources officielles citées :**")
                    for s in m["sources"]:
                        st.markdown(f"- `{s}`")
                
                if m.get("tools_used"):
                    st.markdown(f"**🛠️ Outils exécutés :** {m['tools_used']}")
                
                if m.get("steps"):
                    st.markdown("**📝 Détail des étapes :**")
                    st.json(m["steps"])

# Gestion d'une action en attente de confirmation humaine (Niveau 2)
if st.session_state.pending_action:
    pa = st.session_state.pending_action
    st.warning("⚠️ **Validation humaine requise pour l'action irréversible suivante :**")
    st.json(pa["action_input"])
    
    col_c1, col_c2 = st.columns([1, 4])
    with col_c1:
        if st.button("✅ Confirmer et enregistrer"):
            with st.spinner("Exécution de l'action validée par l'étudiant..."):
                final_res = agent_engine.process(
                    query=pa["query"],
                    user_confirmed=True,
                    state=pa["state"]
                )
                st.session_state.pending_action = None
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_res["response"],
                    "meta": {
                        "level": 2,
                        "latency": final_res["trace"]["latency_seconds"],
                        "tokens": final_res["trace"]["total_tokens"],
                        "status": final_res["status"],
                        "tools_used": final_res["trace"]["tools_used"],
                        "steps": final_res["trace"]["steps"]
                    }
                })
                st.rerun()
    with col_c2:
        if st.button("❌ Annuler l'action"):
            st.session_state.pending_action = None
            st.info("Action annulée.")
            st.rerun()

# Saisie utilisateur
query = st.chat_input("Posez votre question sur les bourses, le logement, les APL ou simulez vos aides...")
if "sample_query" in st.session_state and st.session_state.sample_query:
    query = st.session_state.sample_query
    st.session_state.sample_query = None

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Traitement en cours..."):
            t_start = time.time()
            if level_choice == 0:
                result = level0_model.process(query)
                response_text = result["response"]
                meta = {
                    "level": 0,
                    "latency": result["trace"]["latency_seconds"],
                    "tokens": result["trace"]["total_tokens"],
                    "status": result["trace"]["status"],
                    "sources": [],
                    "steps": result["trace"]["steps"]
                }
            elif level_choice == 1:
                result = rag_engine.process(query)
                response_text = result["response"]
                meta = {
                    "level": 1,
                    "latency": result["trace"]["latency_seconds"],
                    "tokens": result["trace"]["total_tokens"],
                    "status": result["trace"]["status"],
                    "sources": result["sources"],
                    "steps": result["trace"]["steps"]
                }
            else: # level_choice == 2
                result = agent_engine.process(query, user_confirmed=False)
                response_text = result["response"]
                meta = {
                    "level": 2,
                    "latency": result["trace"]["latency_seconds"],
                    "tokens": result["trace"]["total_tokens"],
                    "status": result["status"],
                    "tools_used": result["trace"]["tools_used"],
                    "steps": result["trace"]["steps"]
                }
                if result["status"] == "WAITING_CONFIRMATION":
                    st.session_state.pending_action = {
                        "query": query,
                        "action_to_confirm": result["action_to_confirm"],
                        "action_input": result["action_input"],
                        "state": result["state"]
                    }

            # Enregistrement des statistiques globales
            st.session_state.session_tokens += meta["tokens"]
            st.session_state.session_latencies.append(meta["latency"])

            st.markdown(response_text)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "meta": meta
            })
            st.rerun()
