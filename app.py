"""Streamlit UI for the GIAN knowledge-base RAG system.

    streamlit run app.py
"""
import pandas as pd
import streamlit as st

from gian_kb.config import EMBED_MODEL
from gian_kb.rag import REFUSAL, SYSTEM_PROMPT, GianRAG

st.set_page_config(page_title="GIAN Knowledge Base - RAG", page_icon="🐝", layout="wide")

SAMPLES = [
    "Who developed a method to grow trees with just one litre of water, and how does it work?",
    "Who organised and who supported the 51st Shodhyatra, and when and where did it take place?",
    "How heavy is the Noorjahan mango and who promoted it?",
    "Who built a machine for breaking mahua seeds, and how successful was it in the field trials?",
    "How many sweet potato varieties are attributed to Panchariya?",
    "Who developed the thornless Khejri, and is the innovator's name written the same way in both parts of the article?",
    "Is Dharamveer Khambojji from the 51st Shodhyatra the same person as Shri Dharmveer who built the mahua machine?",
    "Which organisations are associated with both the 51st and the 53rd Shodhyatra in these sources?",
    "Are there GIAN Nidhi student projects about helmets? List them with their institutions.",
    "Where does the information about the Hariyali Handi non-stick clay pots come from?",
    "नूरजहां आम का वजन कितना होता है और इसे किसने संरक्षित किया?",
    "In which year did Himmat Ram Bhambhu receive the Padma Shri?",
    "Who won the Cricket World Cup in 2011?",
]


@st.cache_resource(show_spinner="Connecting to the knowledge base ...")
def load() -> GianRAG:
    return GianRAG()


@st.cache_data(show_spinner=False)
def kb_stats(_rag: GianRAG) -> dict:
    c = _rag.retriever.conn
    q = lambda sql: c.execute(sql).fetchone()[0]
    return {"chunks": q("SELECT count(*) FROM chunks"), "entities": q("SELECT count(*) FROM entities"),
            "relationships": q("SELECT count(*) FROM relationships"),
            "projects": q("SELECT count(*) FROM gian_nidhi_projects"),
            "server": q("SELECT current_setting('server_version')"),
            "host": c.info.host}


with st.sidebar:
    st.header("🐝 GIAN Knowledge Base")
    rag = load()
    stats = kb_stats(rag)
    st.markdown(
        f"**LLM:** `{rag.llm.label}`  \n**Embeddings:** `{EMBED_MODEL}` (BAAI/bge-m3, 1024-d)  \n"
        f"**Vector DB:** PostgreSQL {stats['server']} + pgvector @ `{stats['host']}`  \n"
        f"**KB:** {stats['chunks']} chunks · {stats['entities']} entities · {stats['relationships']} relationships · "
        f"{stats['projects']} GIAN Nidhi records")
    st.markdown("**Sources:** 51st Shodhyatra (Honey Bee 35(3) & 35(4)) · 53rd Shodhyatra presentation (Hindi) · GIAN Nidhi (gian.org)")
    st.divider()
    st.caption("Try a sample question")
    for i, s in enumerate(SAMPLES):
        if st.button(s, key=f"s{i}", use_container_width=True):
            st.session_state["q"] = s

st.title("Ask the GIAN knowledge base")
st.caption("Answers use only retrieved sources; every source line below is rendered from database metadata, "
           f"and unsupported questions get: “{REFUSAL}”")
q = st.text_input("Question", key="q", placeholder="e.g. Who developed the thornless Khejri?")
go = st.button("Ask", type="primary")

if (go or q) and q.strip():
    with st.spinner("Retrieving, generating and verifying ..."):
        res = rag.answer(q)
    badge = {"answered": "🟢 answered", "partial": "🟡 partially answered", "insufficient": "⚪ not in sources"}[res.status]
    st.markdown(f"{badge} · {res.timings.get('total_s')} s · mode: "
                f"`{res.verification.get('answer_mode', 'LLM generation + verification')}`")
    st.markdown(res.markdown)

    with st.expander("Retrieval trace (excerpts considered)"):
        df = pd.DataFrame(res.retrieved)
        if not df.empty:
            cols = [c for c in ["label", "chunk_id", "locator", "dense", "dense_rank", "lexical_rank", "entity_hits",
                                "graph_hits", "keyword_match", "sent_to_llm", "title"] if c in df]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
    with st.expander("Verification"):
        st.json(res.verification)
    with st.expander("Cited source excerpts (full text)"):
        for s in res.sources:
            row = rag.retriever._rows([s["chunk_id"]])[s["chunk_id"]]
            st.markdown(f"**[{s['label']}] {row['locator']}** - {row['source_url']}")
            st.text(row["text"])
            if row["language"] == "hi+en":
                st.caption("Original Hindi (repaired PDF text):")
                st.text(row["text_original"])
            if row["image_text"]:
                st.caption("Text transcribed from images:")
                st.text(row["image_text"])
    with st.expander("System prompt"):
        st.code(SYSTEM_PROMPT, language="text")
