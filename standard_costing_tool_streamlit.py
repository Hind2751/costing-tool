import streamlit as st

st.set_page_config(page_title="Costing Tool — Home", layout="wide")
st.title("Standard Costing Tool — Process Products")

st.page_link("pages/1_Details.py", label="Details — Inputs & Calculations")
st.page_link("pages/2_Summary.py", label="Summary — Totals & Graphs")
st.page_link("pages/3_Dashboard.py", label="Dashboard — Finance & Custom Charts")
