"""Ask the GIAN knowledge base a question from the command line.

    python ask.py "Who developed a method to grow trees with one litre of water?"
    python ask.py --json "..."                     # full structured result (sources, trace, verification)
"""
import argparse
import json
import sys
from dataclasses import asdict

from gian_kb.rag import GianRAG

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+")
    ap.add_argument("--model", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rag = GianRAG(model=a.model)
    res = rag.answer(" ".join(a.question))
    if a.json:
        print(json.dumps(asdict(res), ensure_ascii=False, indent=2, default=str))
    else:
        print(res.markdown)
        print(f"\n_model: {res.model} | status: {res.status} | {res.timings}_")
