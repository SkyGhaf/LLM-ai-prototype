"""
Hotel Kamer Aanbeveling Agent - Web UI (Streamlit)

Start: python -m streamlit run app.py
Vereiste: Ollama actief met llama3.2:1b
"""

import streamlit as st

from agent import create_hotel_agent

st.set_page_config(
    page_title="Hotel Den Haag - Kamer Assistent",
    page_icon="🏨",
    layout="centered",
)

# Hotel-thema styling
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f8f5f0 0%, #efe9e0 100%);
    }
    .hotel-header {
        text-align: center;
        padding: 1.2rem 0 0.4rem 0;
    }
    .hotel-header h1 {
        font-family: Georgia, serif;
        color: #2c3e50;
        margin-bottom: 0;
    }
    .hotel-header p {
        color: #8a7d6b;
        font-style: italic;
    }
    .stChatMessage {
        border-radius: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hotel-header">
        <h1>🏨 Hotel Kamer Assistent</h1>
        <p>Uw persoonlijke hulp bij het vinden van de perfecte kamer</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# De agent bewaart zelf de gespreksstatus (fase + criteria), dus één
# instantie per browsersessie in session_state
if "agent" not in st.session_state:
    with st.spinner("Agent wordt geladen (vectorstore + model)..."):
        st.session_state.agent = create_hotel_agent()
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Welkom! 👋 Ik help u graag de perfecte hotelkamer te vinden. "
                "Vertel me waar u naar op zoek bent - bijvoorbeeld: "
                "*'Ik zoek een kamer voor 2 personen onder de 120 euro'*."
            ),
        }
    ]

# Sidebar met sessie-info en reset
with st.sidebar:
    st.subheader("Gesprek")
    if st.button("🔄 Nieuw gesprek", use_container_width=True):
        del st.session_state["agent"]
        del st.session_state["messages"]
        st.rerun()
    if st.session_state.agent.criteria:
        st.divider()
        st.subheader("Genoteerde wensen")
        for veld, waarde in st.session_state.agent.criteria.items():
            st.caption(f"**{veld}**: {waarde}")
    st.divider()
    st.caption("Sprint 3 - LangChain + Ollama (llama3.2:1b) + FAISS")

# Chatgeschiedenis tonen
for msg in st.session_state.messages:
    avatar = "🧑‍💼" if msg["role"] == "assistant" else "🧳"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Invoer van de gast
if prompt := st.chat_input("Typ uw bericht..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧳"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧑‍💼"):
        with st.spinner("Even denken..."):
            try:
                answer = st.session_state.agent.reageer(prompt)
            except Exception as exc:
                answer = (
                    f"Er is een fout opgetreden: {exc}. "
                    "Kunt u uw vraag anders formuleren?"
                )
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    # Sidebar met genoteerde wensen direct verversen
    st.rerun()
