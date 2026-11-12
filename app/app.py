"""Demo application (a deliverable, due Sun 23:59). Run: make app

Keep it thin: load outputs the pipeline already produced, show the key result,
and let a judge poke at it. All logic lives in src/dh/, not here.
"""

import pandas as pd
import streamlit as st

from dh import leaderboard, load_config
from dh.llm import ask, model, provider

st.set_page_config(page_title="PolyFinances Datathon 2026", layout="wide")
st.title("TODO: project name")
st.caption("TODO: one-sentence problem for the challenge sponsor")

cfg = load_config()

tab_result, tab_ask, tab_runs = st.tabs(["Result", "Ask the analyst", "Experiments"])

with tab_result:
    st.info("TODO: the one chart / table that answers the challenge question.")

with tab_ask:
    st.write(f"LLM: `{provider()}` / `{model()}` (Amazon Bedrock)")
    q = st.text_area("Question", "Explain the main driver of our prediction in plain language.")
    if st.button("Ask"):
        st.write(ask(q, system="You are a financial analyst. Be concise and cite numbers."))

with tab_runs:
    try:
        st.dataframe(leaderboard(cfg), use_container_width=True)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        st.write("No runs yet.")
