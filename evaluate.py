"""Run the evaluation questions through the full RAG pipeline and write a report.

    python evaluate.py                    # local model (Ollama)

Outputs: evaluation/results.json, evaluation/EVALUATION_EXAMPLES.md
Also stores the bge-m3 embedding of every evaluation question in the eval_queries table, so
vector search can be tried from plain SQL (see docs/DATABASE_ACCESS.md).
"""
import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

from gian_kb.config import DATABASE_URL
from gian_kb.embed import embed_texts
from gian_kb.rag import REFUSAL, GianRAG

ROOT = Path(__file__).parent
EVAL = ROOT / "evaluation"


def store_query_embeddings(questions, url=DATABASE_URL):
    vecs = embed_texts([q["q"] for q in questions], cpu=True)
    with psycopg.connect(url, autocommit=True) as conn:
        register_vector(conn)
        conn.execute("DELETE FROM eval_queries")
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO eval_queries VALUES (%s,%s,%s,%s)",
                            [(q["id"], q["q"], q["expect"], np.asarray(v, dtype=np.float32)) for q, v in zip(questions, vecs)])


def check(q, res) -> dict:
    ans = res.answer.lower()
    cited_docs = {s["document_id"] for s in res.sources}
    out = {"refused": REFUSAL.lower() in ans}
    if q["expect"] == "refuse":
        out["pass"] = out["refused"]
        out["reason"] = "returned the insufficiency sentence" if out["pass"] else "answered a question the sources cannot support"
        return out
    inc = [any(alt.lower() in ans for alt in grp.split("|")) for grp in q["must_include"]]
    cit = [any(alt in cited_docs for alt in grp.split("|")) for grp in q["must_cite"]]
    out["include_ok"], out["cite_ok"] = all(inc), all(cit)
    out["pass"] = res.status != "insufficient" and out["include_ok"] and out["cite_ok"]
    missing = [g for g, ok in zip(q["must_include"], inc) if not ok] + [f"cite:{g}" for g, ok in zip(q["must_cite"], cit) if not ok]
    out["reason"] = "ok" if out["pass"] else ("refused" if res.status == "insufficient" else f"missing {missing}")
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    questions = json.loads((EVAL / "questions.json").read_text(encoding="utf-8"))["questions"]
    if a.only:
        questions = [q for q in questions if q["id"] in a.only]
    store_query_embeddings(questions)
    rag = GianRAG(model=a.model)
    rows, t0 = [], time.time()
    for q in questions:
        res = rag.answer(q["q"])
        chk = check(q, res)
        rows.append({"id": q["id"], "category": q["category"], "expect": q["expect"], "check": chk, "result": asdict(res)})
        print(f"{q['id']} {'PASS' if chk['pass'] else 'FAIL'} [{res.status}] {res.timings['total_s']}s - {chk['reason']}")
    passed = sum(r["check"]["pass"] for r in rows)
    summary = {"model": rag.llm.label, "questions": len(rows), "passed": passed,
               "refusal_questions": sum(r["expect"] == "refuse" for r in rows),
               "refusals_correct": sum(r["expect"] == "refuse" and r["check"]["pass"] for r in rows),
               "answer_questions": sum(r["expect"] == "answer" for r in rows),
               "answers_correct": sum(r["expect"] == "answer" and r["check"]["pass"] for r in rows),
               "minutes": round((time.time() - t0) / 60, 1)}
    EVAL.mkdir(exist_ok=True)
    (EVAL / "results.json").write_text(json.dumps({"summary": summary, "results": rows}, ensure_ascii=False, indent=2,
                                                  default=str), encoding="utf-8")
    md = ["# Evaluation examples", "",
          f"Model: **{summary['model']}** | Embeddings: **BAAI/bge-m3 (1024-d)** | Vector DB: **PostgreSQL + pgvector**", "",
          f"Automatic checks passed: **{passed}/{len(rows)}** "
          f"(answerable: {summary['answers_correct']}/{summary['answer_questions']}, "
          f"must-refuse: {summary['refusals_correct']}/{summary['refusal_questions']}).", "",
          "Each check verifies the expected behaviour (answer vs. the exact insufficiency sentence), required facts in the "
          "answer and the cited source document. Retrieval trace = the excerpts given to the model with their dense "
          "similarity and which signals found them.", ""]
    for r in rows:
        res = r["result"]
        md += [f"---", f"## {r['id']} - {r['category']}", f"**Question:** {res['question']}", "",
               f"**Expected:** {r['expect']} | **Check:** {'PASS' if r['check']['pass'] else 'FAIL'} ({r['check']['reason']}) | "
               f"**Status:** {res['status']} | **Time:** {res['timings'].get('total_s')} s", "", res["markdown"], "",
               "<details><summary>Retrieval trace</summary>", "",
               "| Label | Chunk | Locator | Dense sim | Dense rank | Lexical rank | Entity hits |", "|---|---|---|---|---|---|---|"]
        for h in res["retrieved"]:
            md.append(f"| {h['label']} | {h['chunk_id']} | {h['locator'][:70]} | {h['dense']} | {h['dense_rank']} | "
                      f"{h['lexical_rank']} | {', '.join(h['entity_hits'])} |")
        md += ["", f"Gate: `{json.dumps(res['verification'].get('gate'))}`  ",
               f"Verification: attempts={res['verification'].get('attempts', 0)}, remaining problems="
               f"{res['verification'].get('remaining_problems', [])}, removed sentences={res['verification'].get('removed_sentences', [])}",
               "", "</details>", ""]
    (EVAL / "EVALUATION_EXAMPLES.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
