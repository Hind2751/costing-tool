
# pages/4_Help_Chat.py
import streamlit as st
from utils.state import ensure_state
from utils.assistant import answer, render_quick_help_sidebar

st.set_page_config(page_title="Help & Chat", layout="wide")
data = ensure_state(st)
render_quick_help_sidebar(st, data)

st.title("Help & Chat")

if "help_chat" not in st.session_state:
    st.session_state["help_chat"] = [{"role":"assistant","content":"Hi! Ask me anything about using this costing tool. For example: 'How do I import data?' or 'Where do I set the selling price?'."}]

for msg in st.session_state["help_chat"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Type your question…")
if prompt:
    st.session_state["help_chat"].append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    reply = answer(prompt, data)
    st.session_state["help_chat"].append({"role":"assistant","content":reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
