"""Create the pgvector schema and load the knowledge base into PostgreSQL.

Usage:
    python -m gian_kb.db                      # load into DATABASE_URL (from .env)
    python -m gian_kb.db --create-reader      # also create/refresh a read-only login role
                                              # (READER_USER / READER_PASSWORD from .env)
"""
from __future__ import annotations

import argparse
import csv
import json
import os

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from .config import DATABASE_URL, DOCUMENTS, EMBED_MODEL, PROCESSED, ROOT


def locator(c: dict) -> str:
    if c["locator_type"] == "page":
        pp = c["printed_pages"]
        pg = f"p. {pp[0]}" if len(pp) == 1 else f"pp. {pp[0]}-{pp[-1]}"
        pdf = c["pdf_pages"]
        pdf_s = f"PDF page {pdf[0]}" if len(pdf) == 1 else f"PDF pages {pdf[0]}-{pdf[-1]}"
        return f"Honey Bee {c['publication_issue']}, {pg} ({pdf_s} of '{c['source_file']}')"
    if c["locator_type"] == "slide":
        s = c["slides"]
        return f"53rd Shodhyatra presentation, slide {s[0]}" if len(s) == 1 else f"53rd Shodhyatra presentation, slides {s[0]}-{s[-1]}"
    if c["record_ids"]:
        ids = c["record_ids"]
        extra = f" (identical duplicate record(s): {', '.join(map(str, ids[1:]))})" if len(ids) > 1 else ""
        return f"GIAN Nidhi record ID {ids[0]}{extra}"
    return "GIAN Nidhi page text"


def _csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _split(v, sep="; "):
    return [x for x in (v or "").split(sep) if x]


def load(url: str = DATABASE_URL) -> dict:
    chunks = [json.loads(l) for l in (PROCESSED / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    idx = json.loads((PROCESSED / "embeddings_index.json").read_text(encoding="utf-8"))
    vecs = np.load(PROCESSED / "embeddings.npy")
    if idx["chunk_ids"] != [c["chunk_id"] for c in chunks]:
        raise RuntimeError("embeddings are stale - run `python -m gian_kb.embed` first")
    entities = [json.loads(l) for l in (PROCESSED / "entities.jsonl").read_text(encoding="utf-8").splitlines()]
    mentions = _csv(PROCESSED / "entity_mentions.csv")
    rels = _csv(PROCESSED / "relationships.csv")
    insts = _csv(PROCESSED / "gian_nidhi_institutions.csv")
    projects = _csv(PROCESSED / "gian_nidhi_projects.csv")
    dq = _csv(PROCESSED / "data_quality_issues.csv")
    chunk_of_record = {rid: c["chunk_id"] for c in chunks for rid in c["record_ids"]}

    with psycopg.connect(url, autocommit=False) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        register_vector(conn)
        conn.execute((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO documents VALUES (%(document_id)s,%(source)s,%(source_type)s,%(source_url)s,%(source_file)s,
                   %(document_title)s,%(document_title_en)s,%(author)s,%(author_note)s,%(publication_name)s,
                   %(publication_issue)s,%(publication_year)s,%(date_note)s,%(language)s,%(organisations)s,
                   %(organisation_note)s,%(event_id)s,%(locator_unit)s,%(extra)s)""",
                [{**{k: d.get(k) for k in ("document_id", "source", "source_type", "source_url", "source_file", "document_title",
                                         "document_title_en", "author", "author_note", "publication_name", "publication_issue",
                                         "publication_year", "date_note", "language", "organisations", "organisation_note",
                                         "event_id", "locator_unit")},
                  "extra": Jsonb({"pdf_to_printed_page": d.get("pdf_to_printed_page")})} for d in DOCUMENTS.values()])
            rows = []
            for c, v in zip(chunks, vecs):
                meta = {k: v2 for k, v2 in c.items() if k not in ("embedding_text", "text", "text_original", "text_en")}
                rows.append({
                    **{k: c.get(k) for k in ("chunk_id", "document_id", "data_category", "content_type", "language", "title",
                                             "section", "source", "source_url", "document_title", "author", "publication_name",
                                             "publication_issue", "publication_year", "event_id", "locator_type",
                                             "printed_pages", "pdf_pages", "slides", "record_ids", "innovator_names",
                                             "innovation_names", "persons", "organisations", "places", "awards", "events",
                                             "other_entities", "entity_ids", "text", "text_original", "text_en", "image_text",
                                             "embedding_text", "extraction_method", "quality_flags", "conflict_ids", "pii_redacted",
                                             "curation_notes", "retrieved_at", "content_hash", "pipeline_version")},
                    "locator": locator(c), "translation": Jsonb(c.get("translation")), "metadata": Jsonb(meta),
                    "embedding_model": f"{EMBED_MODEL} (BAAI/bge-m3, 1024-d, cosine)", "embedding": v})
            cols = list(rows[0].keys())
            cur.executemany(f"INSERT INTO chunks ({', '.join(cols)}) VALUES ({', '.join('%(' + k + ')s' for k in cols)})", rows)
            cur.executemany(
                "INSERT INTO entities VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [(e["id"], e["type"], e["name"], e.get("aliases", []), e.get("documents", []), e.get("description"),
                  e.get("roles"), e.get("flags"), e.get("link_note"), Jsonb(e.get("attributes") or {})) for e in entities])
            seen, mrows = set(), []
            for m in mentions:
                if (m["chunk_id"], m["entity_id"]) not in seen:
                    seen.add((m["chunk_id"], m["entity_id"]))
                    mrows.append((m["chunk_id"], m["entity_id"], m["surface_form"], m["method"]))
            cur.executemany("INSERT INTO entity_mentions VALUES (%s,%s,%s,%s)", mrows)
            cur.executemany(
                "INSERT INTO relationships VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                [(r["rel_id"], r["subject_id"], r["predicate"], r["object_id"], r["status"],
                  _split(r["evidence_chunk_ids"], " | "), Jsonb(json.loads(r["evidence_locators"] or "[]")), r["note"]) for r in rels])
            cur.executemany(
                "INSERT INTO gian_nidhi_institutions VALUES (%s,%s,%s,%s,%s,%s,%s)",
                [(r["institution_id"], r["canonical_name"], r["match_keys"], int(r["record_count"]), r["name_variants"],
                  r["possible_same_as"], r["reviewed_not_same_as"]) for r in insts])
            cur.executemany(
                "INSERT INTO gian_nidhi_projects VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [(int(p["record_id"]), int(p["sr_no"]) if p["sr_no"].isdigit() else None, p["project_name"],
                  _split(p["participants"]), int(p["participant_count"]), p["abstract"], int(p["abstract_word_count"]),
                  p["institution_name"] or None, p["institution_canonical"] or None, p["institution_id"] or None,
                  p["record_status"], p["duplicate_group_id"] or None, p["duplicate_status"],
                  int(p["duplicate_of"]) if p["duplicate_of"] else None, _split(p["data_quality_flags"]),
                  p["participants_raw"], p["institution_raw"], p["source"], p["source_url"], p["retrieved_at"],
                  chunk_of_record.get(int(p["record_id"]))) for p in projects])
            cur.executemany(
                "INSERT INTO data_quality_issues (source, location, field, issue, action, value_before, value_after) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                [(r["source"], r["location"], r["field"], r["issue"], r["action"], r["value_before"], r["value_after"]) for r in dq])
            conflicts = json.loads((PROCESSED / "conflicts.json").read_text(encoding="utf-8"))
            cur.executemany(
                "INSERT INTO known_conflicts VALUES (%s,%s,%s,%s,%s,%s,%s)",
                [(c["conflict_id"], c["attribute"], c["entity_ids"], c.get("keywords", []), Jsonb(c["values"]),
                  c["chunk_ids"], c.get("note")) for c in conflicts])
        conn.commit()
        conn.execute("ANALYZE")
        counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in ("documents", "chunks", "entities", "entity_mentions", "relationships", "known_conflicts",
                            "gian_nidhi_institutions", "gian_nidhi_projects", "data_quality_issues")}
    return counts


def create_reader(url: str = DATABASE_URL) -> str:
    user = os.getenv("READER_USER", "gian_reader")
    pwd = os.getenv("READER_PASSWORD")
    if not pwd:
        raise SystemExit("set READER_PASSWORD in .env")
    with psycopg.connect(url, autocommit=True) as conn:
        db = conn.execute("SELECT current_database()").fetchone()[0]
        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,)).fetchone()
        q = psycopg.sql
        if exists:
            conn.execute(q.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(q.Identifier(user), q.Literal(pwd)))
        else:
            conn.execute(q.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(q.Identifier(user), q.Literal(pwd)))
        for stmt in ("GRANT CONNECT ON DATABASE {db} TO {u}", "GRANT USAGE ON SCHEMA public TO {u}",
                     "GRANT SELECT ON ALL TABLES IN SCHEMA public TO {u}",
                     "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO {u}",
                     "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {u}",
                     "ALTER ROLE {u} SET default_transaction_read_only = on"):
            conn.execute(q.SQL(stmt).format(db=q.Identifier(db), u=q.Identifier(user)))
    return user


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--create-reader", action="store_true")
    a = ap.parse_args()
    print(json.dumps(load(), indent=2))
    if a.create_reader:
        print("read-only role ready:", create_reader())
