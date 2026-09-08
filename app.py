"""Streamlit demo. Build this last -- a UI over a broken pipeline just hides
the breakage.

    streamlit run app.py
"""
import streamlit as st
import config
from src.chunks import load_chunks
from src.retrieve import BM25Retriever
from src.llm import get_llm
from src.pipeline import answer

st.set_page_config(page_title="Textbook QA", layout="wide")


@st.cache_resource
def load():
    chunks = load_chunks(config.INDEX_DIR / "chunks.jsonl")
    return BM25Retriever(chunks), get_llm()


retriever, llm = load()
st.caption(f"backend: {llm.name}")

q = st.text_input("Ask about a term in the textbook")
if q:
    with st.spinner("..."):
        ans = answer(q, retriever, llm, config.TOP_K)
    st.markdown(ans.text)
    # Showing the retrieved chunks is not a debug affordance -- it is the
    # feature. A student who can check the source learns more than one who
    # is asked to trust the answer.
    with st.expander(f"Sources ({len(ans.chunks)})"):
        for c, s in zip(ans.chunks, ans.scores):
            st.markdown(f"**{c.cite()}**  ·  score {s:.3f}")
            st.text(c.text[:600])
