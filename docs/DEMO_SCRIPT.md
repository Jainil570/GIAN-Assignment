# Screen-recording plan (about 6 minutes)

**Record with:** Windows Game Bar (`Win + Alt + R` to start and stop; saved under *Videos\Captures*) or OBS Studio.
**Before recording:**
* Start Docker (pgvector container `gian-pgvector`) or point `.env` at the shared database.
* Start Ollama, then run `streamlit run app.py`.
* Warm the models once by asking any question.

| # | Show | Say (summary) |
|---|---|---|
| 1 | `README.md` deliverables table | Three sources; the goal is a source-attributed knowledge base. |
| 2 | `docs/DATA_ANALYSIS_REPORT.md` §2-§3 | PDF 2 holds two articles. The Hindi text layer was corrupted and repaired. GIAN Nidhi was collected through its AJAX endpoint. Cross-source entities; look-alike names kept apart. |
| 3 | `data/processed/gian_nidhi_projects.csv` in Excel | Cleaned CSV: raw and clean columns, duplicate groups, quality flags. |
| 4 | psql / DBeaver: `SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id='Q07'), 5);` and `SELECT * FROM v_chunk_citations WHERE chunk_id='SY53-PPT-U26';` | pgvector with 1024-d bge-m3 vectors; every row carries its provenance. |
| 5 | UI: "Who developed a method to grow trees with just one litre of water, and how does it work?" | Two sources cited separately; innovator spelled as in each source; author "not stated". Open the retrieval trace. |
| 6 | UI: "How heavy is the Noorjahan mango and who promoted it?", then the same question in Hindi | Hindi slide answered in English and Hindi; all three weights in the source are reported. |
| 7 | UI: "Who developed the thornless Khejri, and is the innovator's name written the same way in both parts of the article?" | Name variants Prasad / Lal with pages. |
| 8 | UI: "Is Dharamveer Khambojji ... the same person as Shri Dharmveer ...?" | Similar names are not merged; the link is "not established". |
| 9 | UI: "Which organisations are associated with both the 51st and the 53rd Shodhyatra?" | Answer from relationships, with evidence for each event. |
| 10 | UI: "Are there GIAN Nidhi student projects about helmets? List them." | Complete list of all 7 matches from all 640 records. |
| 11 | UI: "In which year did Himmat Ram Bhambhu receive the Padma Shri?" and "Who won the Cricket World Cup in 2011?" | Exact refusal sentence; no year is invented. |
| 12 | `evaluation/EVALUATION_EXAMPLES.md` header and `docs/SYSTEM.md` system prompt | 23/23 checks; model, embeddings, vector DB, prompt. |
