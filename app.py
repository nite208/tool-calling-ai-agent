import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.logging_setup import configure_logging
from src.agent import run_agent

configure_logging()

st.set_page_config(page_title="AI Agent", page_icon="🤖", layout="centered")
st.title("AI Agent")
st.caption("Powered by Groq: supports calculator, weather, and Wikipedia tools.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask me anything...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            for chunk in run_agent(history):
                full_response += chunk
                response_placeholder.markdown(full_response)
        except Exception as exc:
            full_response = f"An unexpected error occurred. Please try again."
            response_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
