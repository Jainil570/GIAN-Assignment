"""Minimal, self-contained example for querying the GIAN knowledge base (PostgreSQL + pgvector).

    pip install "psycopg[binary]" pgvector numpy requests
    set DATABASE_URL=postgresql://gian_reader:<password>@<host>/<db>?sslmode=require
    python examples/query_db.py "Who developed a method to grow trees with one litre of water?"

The question is embedded with BAAI/bge-m3 (1024-d, the model used for the stored vectors) served by
Ollama (`ollama pull bge-m3`). No model at hand? Use the pre-computed question embeddings in the
eval_queries table instead - see the SQL at the bottom of this file / docs/DATABASE_ACCESS.md.
"""
import os
import sys

import numpy as np
import psycopg
import requests
from pgvector.psycopg import register_vector

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gian:gian_local_dev@localhost:5433/gian_kb")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")


def embed(text: str) -> np.ndarray:
    r = requests.post(f"{OLLAMA_URL}/api/embed", json={"model": "bge-m3", "input": [text]}, timeout=120)
    r.raise_for_status()
    v = np.asarray(r.json()["embeddings"][0], dtype=np.float32)
    return v / np.linalg.norm(v)


SEARCH = """
SELECT chunk_id,
       round((1 - (embedding <=> %(q)s))::numeric, 3) AS similarity,
       document_title, coalesce(author, 'not stated in source') AS author,
       publication_name, publication_issue, locator, source_url,
       innovator_names, innovation_names, quality_flags,
       left(text, 400) AS excerpt
FROM chunks
ORDER BY embedding <=> %(q)s
LIMIT %(k)s
"""

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    question = " ".join(sys.argv[1:]) or "Who developed a method to grow trees with one litre of water?"
    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        cur = conn.execute(SEARCH, {"q": embed(question), "k": 5})
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
    print(f"Q: {question}\n")
    for r in rows:
        rec = dict(zip(cols, r))
        print(f"[{rec['similarity']}] {rec['chunk_id']}  |  {rec['locator']}")
        print(f"    title: {rec['document_title']}  |  author: {rec['author']}")
        print(f"    innovators: {rec['innovator_names']}  |  innovations: {rec['innovation_names']}")
        print(f"    url: {rec['source_url']}  |  flags: {rec['quality_flags']}")
        print(f"    {rec['excerpt'][:300]}...\n")

# Pure SQL alternative (no embedding model needed) - pre-computed bge-m3 question vectors:
#   SELECT query_id, query_text FROM eval_queries;
#   SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id = 'Q07'), 5);
#   SELECT * FROM keyword_chunks('Noorjahan mango', 5);
#   SELECT * FROM entity_profile('PER-SUNDARAM-VERMA');
