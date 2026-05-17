import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="AI Interview Copilot", layout="wide")

st.title("AI Interview Copilot")
st.caption("Production-track MVP: resume-aware AI interview practice.")

with st.sidebar:
    st.header("Session")
    st.text_input("Target role", value="AI Engineer")
    st.selectbox("Interview mode", ["technical", "behavioral", "hr", "dsa"])
    st.selectbox("Difficulty", ["beginner", "intermediate", "advanced"], index=1)

st.subheader("Backend Health")

try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    response.raise_for_status()
    st.success(f"API status: {response.json()['status']}")
except requests.RequestException as exc:
    st.error(f"API is not reachable yet: {exc}")

st.subheader("Resume Upload")
st.file_uploader("Upload PDF or DOCX resume", type=["pdf", "docx"])

st.info(
    "Next sprint: connect authentication, upload API, resume parsing, and question generation."
)
