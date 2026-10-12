"""Run the whole data pipeline end to end.

    python run_pipeline.py                 # scrape -> clean -> extract -> build -> embed -> load DB
    python run_pipeline.py --skip-scrape   # reuse data/raw/gian_nidhi (offline / reproducible)
    python run_pipeline.py --create-reader # also create the read-only DB role (READER_USER/READER_PASSWORD)
"""
import argparse
import json
import sys
import time

from gian_kb import build_kb, clean_gian_nidhi, db, embed, extract_pdfs, scrape_gian_nidhi


def step(name, fn):
    t = time.time()
    print(f"\n=== {name}", flush=True)
    out = fn()
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str)[:1500] if out is not None else "done",
          f"\n({time.time() - t:.1f} s)", flush=True)
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-scrape", action="store_true")
    ap.add_argument("--skip-db", action="store_true")
    ap.add_argument("--create-reader", action="store_true")
    a = ap.parse_args()
    if not a.skip_scrape:
        step("1. Scrape GIAN Nidhi (WP Data Access AJAX endpoint)", scrape_gian_nidhi.fetch)
    step("2. Clean GIAN Nidhi -> CSV", clean_gian_nidhi.main)
    step("3. Extract PDFs (layout-aware EN, repaired Hindi)",
         lambda: {"sy51_paragraphs": len(extract_pdfs.extract_sy51()), "sy53_slides": len(extract_pdfs.extract_sy53())})
    step("4. Build knowledge base (chunks, entities, mentions, relationships)", build_kb.main)
    step("5. Embed chunks (bge-m3, 1024-d)", embed.main)
    if not a.skip_db:
        step("6. Load PostgreSQL + pgvector", db.load)
        if a.create_reader:
            step("7. Read-only role", db.create_reader)
