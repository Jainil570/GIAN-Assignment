# GIAN AI Knowledge Base: data linking, pgvector and source-attributed RAG

This project builds a queryable, source-attributed knowledge base from three GIAN sources:

* **PDF 1:** the 53rd Shodhyatra presentation (Hindi, 94 slides).
* **PDF 2:** the 51st Shodhyatra articles from two issues of the Honey Bee newsletter.
* **GIAN Nidhi:** 640 student projects collected from gian.org.

The sources are analysed, linked and cleaned, then structured into chunks, entities, relationships and known conflicts. They are embedded with **BAAI/bge-m3** into **PostgreSQL + pgvector**. A RAG system answers questions **only** from retrieved sources, with page-, slide- or record-level attribution, and says *"The available sources do not provide sufficient information to answer this."* when it cannot.

**Submitted by:** Jainil ([github.com/Jainil570](https://github.com/Jainil570)) · **Demo video:** [screen recording (Google Drive)](https://drive.google.com/drive/folders/1zdsOBzecotO1SLdw9mmomBYVea8Yga1_?usp=sharing)

## For evaluators: start here
1. **Report:** [`docs/DATA_ANALYSIS_REPORT.pdf`](docs/DATA_ANALYSIS_REPORT.pdf): structure, cross-source entities, gaps, linking fields, cleaning decisions.
2. **Query the shared database:** read-only login in [`docs/DATABASE_ACCESS.md`](docs/DATABASE_ACCESS.md). Try `SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id='Q07'), 5);`, which needs no model.
3. **See the RAG answers:** [`evaluation/EVALUATION_EXAMPLES.md`](evaluation/EVALUATION_EXAMPLES.md) (23 questions, 23/23 checks), [`docs/screenshots/`](docs/screenshots/) and the demo video.
4. **System details and the full prompt:** [`docs/SYSTEM.md`](docs/SYSTEM.md).

## Deliverables

| Assignment item | Where |
|---|---|
| 1. Data Analysis Report (structure, gaps, linking fields, cleaning decisions) | [`docs/DATA_ANALYSIS_REPORT.md`](docs/DATA_ANALYSIS_REPORT.md) (+ `.pdf`) |
| CSV dataset from GIAN Nidhi | [`data/processed/gian_nidhi_projects.csv`](data/processed/gian_nidhi_projects.csv) (640 records, 20 columns) + [`gian_nidhi_institutions.csv`](data/processed/gian_nidhi_institutions.csv) |
| 2. pgvector database: model, dimension, metadata schema, access, query code | **Shared on Neon (read-only login inside)**: [`docs/DATABASE_ACCESS.md`](docs/DATABASE_ACCESS.md), [`examples/query_db.py`](examples/query_db.py), [`sql/example_queries.sql`](sql/example_queries.sql) |
| Fallback: methodology, chunking script, embedding script, sample vectors | [`gian_kb/`](gian_kb/) (`extract_pdfs.py`, `devanagari.py`, `build_kb.py`, `embed.py`), [`data/processed/sample_vector_records.jsonl`](data/processed/sample_vector_records.jsonl), `data/export/gian_kb.dump` |
| 3. RAG system + evaluation examples | `app.py` (UI), `ask.py` (CLI), [`evaluation/EVALUATION_EXAMPLES.md`](evaluation/EVALUATION_EXAMPLES.md) (23 questions, 23/23 checks), [`docs/screenshots/`](docs/screenshots/), [demo video](https://drive.google.com/drive/folders/1zdsOBzecotO1SLdw9mmomBYVea8Yga1_?usp=sharing), recording plan [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |
| 5. System (LLM, embedding model, vector DB, complete system prompt) | [`docs/SYSTEM.md`](docs/SYSTEM.md) |

## Quick start (Windows / macOS / Linux)

Prerequisites: Python 3.10+ and [Ollama](https://ollama.com). For the database, use the shared Neon URL from `docs/DATABASE_ACCESS.md` (read-only; enough for `ask.py`, `app.py` and `examples/query_db.py`) or Docker for a local copy.

```bash
python -m venv .venv && .venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
ollama pull bge-m3                                      # embeddings (1024-d)
ollama pull qwen2.5:7b-instruct-q4_K_M                  # local answer model
copy .env.example .env                                  # set DATABASE_URL (local docker or shared DB)

# local database (skip if you use the shared one)
docker run -d --name gian-pgvector -e POSTGRES_USER=gian -e POSTGRES_PASSWORD=gian_local_dev -e POSTGRES_DB=gian_kb -p 5433:5432 pgvector/pgvector:pg17
python run_pipeline.py                                  # scrape -> clean -> extract -> build -> embed -> load

python ask.py "Who developed the thornless Khejri, and is the name written the same way in both parts?"
streamlit run app.py                                    # UI at http://localhost:8501
python evaluate.py                                      # 23 evaluation questions -> evaluation/
```
To use a different local model, set `LLM_MODEL` in `.env` (any Ollama chat model).

## Repository layout
```
gian_kb/
  scrape_gian_nidhi.py   collect GIAN Nidhi through the page's own AJAX endpoint (raw response kept)
  clean_gian_nidhi.py    dedupe, repair text, split participants, canonicalise institutions, duplicate groups -> CSV
  devanagari.py          deterministic repair of the corrupted Hindi text layer (glyph map + i-matra/reph reordering)
  extract_pdfs.py        layout-aware extraction (3-column newsletter; hidden-text detection in the deck)
  build_kb.py            chunks + metadata, entities, mentions, relationships, known conflicts
  embed.py               bge-m3 embeddings (cached by content hash), sample vector records
  db.py                  schema + load into PostgreSQL/pgvector, read-only role
  retrieval.py           hybrid retrieval: dense + full-text + entity + relation-aware, RRF fusion
  rag.py                 gating, generation, verification, structured answer paths, attribution
  llm.py                 answer model (Ollama)
sources/                 the two assignment PDFs (not in git: download links in sources/README.md)
data/raw/                GIAN Nidhi page snapshot + raw API rows + fetch log
data/interim/            extracted paragraphs (51st) and repaired slides (53rd)
data/curated/            hand curation: slide units + translations, entities, relationships, conflicts, institution review
data/processed/          CSVs, chunks.jsonl, entities, mentions, relationships, embeddings, data-quality log
sql/                     schema.sql, example_queries.sql
docs/                    report, database access, system card, demo script, screenshots
evaluation/              questions.json, results.json, EVALUATION_EXAMPLES.md
```

## Design in one paragraph
Answers are only as trustworthy as the structure underneath them, so most of the work is in the data:

* **One document per article.** The two Honey Bee articles in PDF 2 are separate documents, so citations name the right issue and printed page.
* **Repaired Hindi.** The deck's corrupted text layer is repaired deterministically, translated faithfully, and stored next to the Hindi original.
* **Conservative linking.** Spelling variants of a person become aliases of one entity only when tied to the same unique innovation. Look-alike names across sources are explicitly marked **unverified** or **distinct**.
* **Conflicts are kept.** Conflicting values are stored with every value and its location, never silently resolved.
* **Every chunk carries full provenance.**

The RAG layer then retrieves with four signals. It answers list, identity, name-variant, "both" and attribution questions directly from that structure. It checks every generated sentence (names present, numbers co-occurring with their subject, citations repaired). It renders the attribution block from metadata, so sources, pages and URLs cannot be invented.
