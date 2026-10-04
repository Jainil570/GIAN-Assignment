"""Generate embeddings for every chunk with BAAI/bge-m3 (1024-d, multilingual).

bge-m3 is served locally by Ollama (`ollama pull bge-m3`), so no API key is needed and the
GIAN team can embed queries with exactly the same model. Each chunk's ``embedding_text``
(contextual header + entity line + text; Hindi chunks carry both the English translation
and the Hindi original) is embedded once; vectors are cached by content hash so re-runs
only embed changed chunks.

Outputs (data/processed/): embeddings.npy (float32, L2-normalised, row order = chunks.jsonl),
embeddings_index.json, sample_vector_records.jsonl
"""
from __future__ import annotations

import json
import time

import numpy as np
import requests

from .config import EMBED_DIM, EMBED_MODEL, OLLAMA_URL, PROCESSED


def embed_texts(texts: list[str], batch: int = 8, cpu: bool = False) -> np.ndarray:
    """cpu=True keeps bge-m3 off the GPU (used for queries, so the answer LLM can stay in VRAM)."""
    out = []
    opts = {"num_ctx": 8192, **({"num_gpu": 0} if cpu else {})}
    for i in range(0, len(texts), batch):
        for attempt in range(3):
            try:
                r = requests.post(f"{OLLAMA_URL}/api/embed",
                                  json={"model": EMBED_MODEL, "input": texts[i:i + batch], "truncate": True,
                                        "options": opts, "keep_alive": "30m"},
                                  timeout=600)
                r.raise_for_status()
                out.extend(r.json()["embeddings"])
                break
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(3)
    arr = np.asarray(out, dtype=np.float32)
    arr /= np.linalg.norm(arr, axis=1, keepdims=True)
    if arr.shape[1] != EMBED_DIM:
        raise ValueError(f"expected {EMBED_DIM}-d vectors, got {arr.shape[1]}")
    return arr


def embed_query(text: str) -> list[float]:
    return embed_texts([text], cpu=True)[0].tolist()


def main() -> dict:
    chunks = [json.loads(l) for l in (PROCESSED / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    cache: dict[str, np.ndarray] = {}
    idx_path, emb_path = PROCESSED / "embeddings_index.json", PROCESSED / "embeddings.npy"
    if idx_path.exists() and emb_path.exists():
        old = json.loads(idx_path.read_text(encoding="utf-8"))
        if old.get("model") == EMBED_MODEL:
            vecs = np.load(emb_path)
            cache = {h: vecs[i] for i, h in enumerate(old["content_hashes"])}
    todo = [c for c in chunks if c["content_hash"] not in cache]
    t0 = time.time()
    if todo:
        new = embed_texts([c["embedding_text"] for c in todo])
        for c, v in zip(todo, new):
            cache[c["content_hash"]] = v
    mat = np.stack([cache[c["content_hash"]] for c in chunks]).astype(np.float32)
    np.save(emb_path, mat)
    idx_path.write_text(json.dumps({"model": EMBED_MODEL, "model_hf": "BAAI/bge-m3", "dim": EMBED_DIM,
                                    "normalised": True, "chunk_ids": [c["chunk_id"] for c in chunks],
                                    "content_hashes": [c["content_hash"] for c in chunks]}, indent=1), encoding="utf-8")

    # sample vector records (deliverable): a few records per source with full metadata + full vector
    picks = []
    for doc in ("SY51-HB-P1", "SY51-HB-P2", "SY53-PPT", "GIAN-NIDHI"):
        picks += [i for i, c in enumerate(chunks) if c["document_id"] == doc][:3]
    with open(PROCESSED / "sample_vector_records.jsonl", "w", encoding="utf-8") as f:
        for i in picks:
            c = {k: v for k, v in chunks[i].items() if k != "embedding_text"}
            c["embedding_model"] = f"{EMBED_MODEL} (BAAI/bge-m3)"
            c["embedding_dim"] = EMBED_DIM
            c["embedding"] = [round(float(x), 6) for x in mat[i]]
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return {"chunks": len(chunks), "embedded_now": len(todo), "seconds": round(time.time() - t0, 1),
            "shape": list(mat.shape)}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
