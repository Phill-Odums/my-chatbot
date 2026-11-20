import os

import streamlit as st
from google import genai
from google.genai.errors import APIError
from streamlit.errors import StreamlitSecretNotFoundError

MODEL_NAME = "gemini-3.1-flash-lite"
key = ""

def get_api_key():
    if key:
        return key

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    try:
        secrets = st.secrets
        gemini_secrets = secrets.get("gemini", {})
        return (
            secrets.get("GEMINI_API_KEY")
            or gemini_secrets.get("api_key")
            or gemini_secrets.get("key")
        )
    except StreamlitSecretNotFoundError:
        return None


st.set_page_config(
    page_title="Gemini Chat",
    page_icon="✦",
    layout="centered",
)

st.markdown(
    """
    <style>
    h1 { letter-spacing: -0.035em; }
    [data-testid="stChatMessage"] {
        border: 1px solid rgba(79, 70, 229, 0.10);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.65rem;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 12px;
    }
    @media (max-width: 640px) {
        [data-testid="stChatMessage"] {
            padding: 0.65rem 0.8rem;
        }
    }
    .app-caption {
        color: var(--text-color);
        opacity: 0.68;
        margin-top: -0.55rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("PHILLZ Chatbot")
st.markdown(
    '<p class="app-caption">A focused space to think, write, and explore.</p>',
    unsafe_allow_html=True,
)

api_key = get_api_key()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    st.session_state.client = None
    st.session_state.chat = None
elif "chat" not in st.session_state:
    st.session_state.chat = None

with st.sidebar:
    st.subheader("Conversation")
    if st.button("Start a new chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat = None
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.messages:
    st.markdown("### Start a conversation")
    st.caption("Ask a question, explore an idea, or get help with a task.")

if not api_key:
    st.info(
        "Gemini is not configured yet. Set `GEMINI_API_KEY` in your environment "
        "or add `GEMINI_API_KEY = \"...\"` to `.streamlit/secrets.toml`, then "
        "reload the app."
    )
    st.chat_input("Add a GEMINI_API_KEY to begin", disabled=True)
    st.stop()

if st.session_state.chat is None:
    if st.session_state.client is None:
        st.session_state.client = genai.Client(api_key=api_key)
    st.session_state.chat = st.session_state.client.chats.create(model=MODEL_NAME)

prompt = st.chat_input("Drop your prompt here and press Enter for the AI to respond...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            for chunk in st.session_state.chat.send_message_stream(prompt):
                chunk_text = getattr(chunk, "text", None)
                if chunk_text:
                    full_response += chunk_text
                    response_placeholder.markdown(full_response + "▌")

            if full_response:
                response_placeholder.markdown(full_response)
            else:
                full_response = "Gemini returned no text for that prompt."
                response_placeholder.markdown(full_response)
        except APIError as error:
            response_placeholder.empty()
            st.error(f"Gemini request failed: {error}")
        except RuntimeError:
            response_placeholder.empty()
            st.session_state.client = None
            st.session_state.chat = None
            st.session_state.messages = []
            st.error(
                "The Gemini session ended unexpectedly. Your conversation was "
                "reset; please send your prompt again."
            )
        else:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

