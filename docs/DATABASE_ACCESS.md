# Database access: PostgreSQL + pgvector

| | |
|---|---|
| Embedding model | **BAAI/bge-m3** (Ollama tag `bge-m3`), multilingual |
| Dimension | **1024**, L2-normalised, cosine distance (`<=>`, index `vector_cosine_ops`) |
| What was embedded | `chunks.embedding_text` = provenance header + title + entity line + text (Hindi units: English translation **and** Hindi original) + image text |
| Database | Shared: **Neon, PostgreSQL 18.6 + pgvector 0.8.6**. Local: PostgreSQL 17 + pgvector 0.8.7 (Docker). HNSW `m=16, ef_construction=64`, `pg_trgm`, full-text indexes |
| Size | 651 chunks / vectors; 2,697 entities; 3,695 mentions; 3,287 relationships; 640 GIAN Nidhi records |

## 1. Connect

**Shared hosted database: Neon (PostgreSQL 18.6 + pgvector 0.8.6), read-only login for evaluators**

| | |
|---|---|
| Host | `ep-quiet-feather-azuif6j9.c-3.ap-southeast-1.aws.neon.tech` |
| Port | `5432` |
| Database | `neondb` |
| User | `gian_reader` (read-only: SELECT on all tables, EXECUTE on helper functions; writes are rejected) |
| Password | `gk_AUtuV6fNdslJP785FPU1EQOf` |
| SSL | required (`sslmode=require`) |

```
DATABASE_URL=postgresql://gian_reader:gk_AUtuV6fNdslJP785FPU1EQOf@ep-quiet-feather-azuif6j9.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
psql "postgresql://gian_reader:gk_AUtuV6fNdslJP785FPU1EQOf@ep-quiet-feather-azuif6j9.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
```
Pooled endpoint (for many concurrent connections): replace the host with `ep-quiet-feather-azuif6j9-pooler.c-3.ap-southeast-1.aws.neon.tech`.
The free-tier compute sleeps when idle; the first connection may take a second or two to wake it.

**Local copy (Docker, same content):**
```
DATABASE_URL=postgresql://gian:gian_local_dev@localhost:5433/gian_kb
```

Any PostgreSQL client works (psql, DBeaver, pgAdmin, Python `psycopg`). The read-only role can `SELECT` from all tables and call the helper functions.

## 2. Query without running any model (pure SQL)

Every evaluation question is stored with its bge-m3 embedding in `eval_queries`, so vector search can be tried immediately:

```sql
SELECT query_id, query_text FROM eval_queries ORDER BY query_id;

-- top-5 chunks for Q07 ("How heavy is the Noorjahan mango and who promoted it?")
SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id = 'Q07'), 5);

-- raw pgvector operator with attribution columns
SELECT c.chunk_id, round((1 - (c.embedding <=> q.embedding))::numeric, 3) AS similarity,
       c.locator, c.source_url, coalesce(c.author, 'not stated in source') AS author,
       c.innovator_names, c.innovation_names
FROM chunks c, (SELECT embedding FROM eval_queries WHERE query_id = 'Q01') q
ORDER BY c.embedding <=> q.embedding LIMIT 5;

SELECT * FROM keyword_chunks('thornless Khejri grafting', 5);      -- full-text search
SELECT * FROM entity_profile('PER-PANCHARIYA');                    -- relationships + evidence
SELECT * FROM v_chunk_citations WHERE chunk_id = 'SY53-PPT-U26';   -- "where did this come from?"
```
More: `sql/example_queries.sql` (12 queries, all tested).

## 3. Query from Python (your own question)

```bash
pip install "psycopg[binary]" pgvector numpy requests
ollama pull bge-m3                       # same model as the stored vectors
set DATABASE_URL=<connection string from section 1>
python examples/query_db.py "Who developed a method to grow trees with one litre of water?"
```

Core of `examples/query_db.py`:
```python
import numpy as np, psycopg, requests
from pgvector.psycopg import register_vector

def embed(text):
    r = requests.post("http://127.0.0.1:11434/api/embed", json={"model": "bge-m3", "input": [text]})
    v = np.asarray(r.json()["embeddings"][0], dtype=np.float32)
    return v / np.linalg.norm(v)

with psycopg.connect(DATABASE_URL) as conn:
    register_vector(conn)
    rows = conn.execute("""
        SELECT chunk_id, 1 - (embedding <=> %(q)s) AS similarity, locator, source_url,
               document_title, author, innovator_names, innovation_names, left(text, 400)
        FROM chunks ORDER BY embedding <=> %(q)s LIMIT 5""", {"q": embed(question)}).fetchall()
```
For the full RAG answer (hybrid retrieval, verification, attribution) run `python ask.py "..."` or `streamlit run app.py` with the same `DATABASE_URL`.

## 4. Tables

| Table | Purpose |
|---|---|
| `documents` | 4 logical source documents: source URL, title, publication/issue, year, author (NULL = not stated) + `author_note`, organisations |
| `chunks` | **retrieval units with full metadata + `embedding vector(1024)`** |
| `entities` | persons, organisations, institutions, places, innovations/practices, events, awards, projects; `aliases` = exact source spellings |
| `entity_mentions` | which chunk mentions which entity, with the surface form used there |
| `relationships` | typed edges (`innovator_of`, `organised_by`, `logo_shown`, `possible_same_as`, `distinct_from`, ...) with `status` (stated / probable / unverified / distinct) and evidence chunk ids |
| `known_conflicts` | facts stated with different values, with every value and its locator |
| `gian_nidhi_projects`, `gian_nidhi_institutions` | the cleaned GIAN Nidhi table (= the CSV deliverable) + canonical institutions |
| `data_quality_issues` | every cleaning action / flag |
| `eval_queries` | evaluation questions with pre-computed bge-m3 embeddings |

## 5. Metadata schema of a chunk (`chunks`)

| Field | Meaning | Example |
|---|---|---|
| `chunk_id` | stable id: `SY51-HB-P1-C02`, `SY53-PPT-U26`, `GIAN-NIDHI-R0037` | `SY53-PPT-U26` |
| `document_id` | source document | `SY53-PPT` |
| `source` | source description | "53rd Shodhyatra presentation (assignment PDF 1)" |
| `source_url` | Drive link / gian.org URL | `https://drive.google.com/file/d/1cS7fMCNjoyD1qnZCC5wOwRUDypQVHX0Z/view` |
| `document_title` | title as printed | "53 वीं शोधयात्रा: भूरीमाटी ... (दिनांक: 04 से 10 जून, 2025)" |
| `author` | author if stated, else NULL (see `documents.author_note`) | NULL |
| `publication_name`, `publication_issue`, `publication_year` | e.g. Honey Bee, "Vol 35 (3) July - September 2024", 2024 | |
| `event_id` | `EVT-SY51` / `EVT-SY53` | `EVT-SY53` |
| `data_category` | `shodhyatra_report` / `shodhyatra_presentation` / `student_project` / `web_page_context` | |
| `content_type` | `narrative` / `image_text` / `slide_unit` / `record` / `web_page_context` | `slide_unit` |
| `section` | article heading / deck section | "Technological Innovations & Traditional Practice" |
| `locator_type`, `printed_pages`, `pdf_pages`, `slides`, `record_ids` | exact position in the source | `slide`, `{48,49}` |
| `locator` | human-readable citation | "53rd Shodhyatra presentation, slides 48-49" |
| `innovator_names`, `innovation_names` | innovators and innovations in the chunk (GIAN Nidhi: project team and title) | `{Isak Mansuri}`, `{Noorjahan mango}` |
| `persons`, `organisations`, `places`, `awards`, `events`, `other_entities`, `entity_ids` | all linked entities | |
| `text` | display text (English; translation for Hindi slides) | |
| `text_original` | verbatim source text (repaired Hindi for the deck) | "[स्लाइड 48] "नूरजहां" आम की वैरायटी ..." |
| `text_en`, `image_text` | English text; text transcribed from images | |
| `embedding_text` | exactly what was embedded | |
| `extraction_method` | how the text was obtained | "pdf_text_layer + deterministic Devanagari repair + manual review ..." |
| `translation` (jsonb) | source/target language and method | `{"source_language":"hi","target_language":"en",...}` |
| `quality_flags` | e.g. `conflicting_values`, `name_variant`, `hidden_text_in_pdf`, `visual_transcription`, `pii_redacted`, `probable_duplicate` | `{conflicting_values}` |
| `conflict_ids` | known conflicts touching the chunk | `{CF-01}` |
| `curation_notes`, `retrieved_at`, `content_hash`, `pipeline_version`, `metadata` (jsonb, everything) | | |
| `embedding` | `vector(1024)` | |

## 6. Rebuild or host your own copy
```bash
docker run -d --name gian-pgvector -e POSTGRES_USER=gian -e POSTGRES_PASSWORD=gian_local_dev \
    -e POSTGRES_DB=gian_kb -p 5433:5432 pgvector/pgvector:pg17
python run_pipeline.py --skip-scrape        # rebuild everything from the sources, or:
pg_restore -d "postgresql://gian:gian_local_dev@localhost:5433/gian_kb" --no-owner data/export/gian_kb.dump
```

## 7. If the shared database is not reachable
Every artefact needed to inspect the implementation is in the repository:
* `docs/DATA_ANALYSIS_REPORT.md`: preprocessing and structuring method.
* `gian_kb/extract_pdfs.py`, `gian_kb/devanagari.py`, `gian_kb/build_kb.py`: the complete chunking scripts.
* `gian_kb/embed.py`: the embedding script.
* `data/processed/sample_vector_records.jsonl`: sample vector records with full metadata and 1024-d vectors.
* `data/processed/embeddings.npy` + `embeddings_index.json`: all 651 vectors.
* `data/processed/chunks.jsonl`: all chunks with metadata.
* `data/export/gian_kb.dump`: full database dump.
