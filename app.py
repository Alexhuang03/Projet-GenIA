"""
Interface Streamlit - SEMAINE 1 (2 – 8 nov.)
Assistant Aides Étudiantes & CROUS · Niveau 0 : LLM Seul (Baseline à battre)
Mineur IA Générative 2026 · Dr. Issam Falih
"""
import streamlit as st
import time
from src.llm_client import UnifiedLLMClient
from src.baseline.level0_llm import Level0LLM, SYSTEM_PROMPT_LEVEL_0

st.set_page_config(
    page_title="Semaine 1 · Assistant Aides Étudiantes (Niveau 0)",
    page_icon="🎓",
    layout="wide"
)

# Initialisation du client LLM
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

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_tokens" not in st.session_state:
    st.session_state.session_tokens = 0
if "session_latencies" not in st.session_state:
    st.session_state.session_latencies = []

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Paramètres Semaine 1")
    
    st.info("**Progression du projet :**\n- 🟢 **Niveau 0 : LLM seul (Semaine 1)**\n- ⏳ Niveau 1 : RAG (Semaine 2)\n- ⏳ Niveau 2 : Agent outillé (Semaine 3)\n- ⏳ Niveau 3 : Extension (Semaine 4)")

    st.markdown("---")
    st.subheader("🔌 Fournisseur LLM")
    provider_choice = st.selectbox(
        "Fournisseur :",
        ["mock", "gemini", "groq", "openai"],
        format_func=lambda x: {
            "mock": "Mode Mock Hors-ligne (Instant)",
            "gemini": "Google Gemini (gemini-2.5-flash)",
            "groq": "Groq Cloud (Llama 3.3)",
            "openai": "OpenAI (GPT-4o-mini)"
        }[x]
    )

    custom_key = ""
    if provider_choice != "mock":
        custom_key = st.text_input(
            f"Clé API {provider_choice.capitalize()} :",
            type="password",
            help="Optionnel si déjà définie dans .env"
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
        st.session_state.session_tokens = 0
        st.session_state.session_latencies = []
        st.rerun()

# Modèle Niveau 0
client = get_llm_client(provider_choice, custom_key)
level0_model = Level0LLM(client)

# --- ZONE CENTRALE ---
st.header("🎓 Assistant Aides Étudiantes & CROUS")
st.subheader("Semaine 1 : Niveau 0 (LLM seul — La référence à battre)")
st.caption("Mineur IA Générative 2026 · Dr. Issam Falih")

st.warning(
    "⚠️ **Objectif pédagogique du Niveau 0** : Observer le comportement d'un LLM généraliste "
    "doté d'un prompt soigné, mais **sans documents ni outils**. "
    "Le modèle produit des réponses plausibles mais invérifiables, hallucine sur les barèmes exacts "
    "et ne s'abstient jamais. C'est cette faiblesse mesurée qui justifiera le passage au RAG en Semaine 2."
)

with st.expander("📜 Voir le System Prompt soigné du Niveau 0"):
    st.code(SYSTEM_PROMPT_LEVEL_0, language="text")

# Suggestions de tests
st.markdown("**Suggestions de questions pour tester les limites du Niveau 0 :**")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("❓ Montant exact de l'échelon 0bis"):
        st.session_state.sample_query = "Quel est le montant annuel de l'échelon 0bis de la bourse CROUS ?"
with c2:
    if st.button("❓ Barème de distance pour 2 points"):
        st.session_state.sample_query = "À quelle distance du domicile familial obtient-on 2 points de charge pour l'éloignement ?"
with c3:
    if st.button("❓ Question hors-sujet (subvention voilier)"):
        st.session_state.sample_query = "Quelle est la subvention du CROUS pour l'achat d'un voilier ou yacht de plaisance ?"

# Affichage des messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg and msg["meta"]:
            m = msg["meta"]
            with st.expander("🔍 Observabilité & Traces de la requête"):
                cols = st.columns(3)
                cols[0].metric("Latence", f"{m.get('latency', 0.0):.3f}s")
                cols[1].metric("Tokens", m.get("tokens", 0))
                cols[2].metric("Statut", m.get("status", "SUCCESS"))
                if m.get("steps"):
                    st.markdown("**Traces d'exécution :**")
                    st.json(m["steps"])

# Saisie utilisateur
query = st.chat_input("Posez votre question...")
if "sample_query" in st.session_state and st.session_state.sample_query:
    query = st.session_state.sample_query
    st.session_state.sample_query = None

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Génération de la réponse par le Niveau 0..."):
            result = level0_model.process(query)
            response_text = result["response"]
            meta = {
                "level": 0,
                "latency": result["trace"]["latency_seconds"],
                "tokens": result["trace"]["total_tokens"],
                "status": result["trace"]["status"],
                "steps": result["trace"]["steps"]
            }

            st.session_state.session_tokens += meta["tokens"]
            st.session_state.session_latencies.append(meta["latency"])

            st.markdown(response_text)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "meta": meta
            })
            st.rerun()
