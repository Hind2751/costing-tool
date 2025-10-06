# pages/4_Help_Chat.py
import streamlit as st
from utils.state import ensure_state
from utils.assistant import answer, render_quick_help_sidebar

st.set_page_config(page_title="Help & Chat", layout="wide")
data = ensure_state(st)
render_quick_help_sidebar(st, data)

st.title("Help & Chat")

# Quick chips (actions + definitions)
cols = st.columns(8)
chips = [
    "Add a utility", "Enter CAPEX items", "Set selling price", "Quick import a section",
    "What is NPV?", "What is IRR?", "What is Payback?", "What is CAPEX?"
]
clicked = None
for i, c in enumerate(cols):
    if c.button(chips[i], key=f"chip_{i}"):
        clicked = chips[i]

if "help_chat" not in st.session_state:
    st.session_state["help_chat"] = [{"role":"assistant","content":"Hi! Ask anything or tap a quick action/definition above."}]

for msg in st.session_state["help_chat"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if clicked:
    st.session_state["help_chat"].append({"role":"user","content":clicked})
    with st.chat_message("user"):
        st.markdown(clicked)
    reply = answer(clicked, data)
    st.session_state["help_chat"].append({"role":"assistant","content":reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

prompt = st.chat_input("Type your question…")
if prompt:
    st.session_state["help_chat"].append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    reply = answer(prompt, data)
    st.session_state["help_chat"].append({"role":"assistant","content":reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
