# System card: GIAN knowledge-base RAG

| | |
|---|---|
| **Model (answer generation)** | `qwen2.5:7b-instruct` (Q4_K_M, 7.6B parameters), served locally by **Ollama**, temperature 0, JSON-schema-constrained output. |
| **Embedding model** | **BAAI/bge-m3** (`bge-m3` in Ollama), **1024 dimensions**, L2-normalised, cosine distance. Multilingual, so Hindi slides and English questions share one vector space. |
| **Vector database** | **PostgreSQL + pgvector** (HNSW index, `vector_cosine_ops`), plus PostgreSQL full-text search (English + simple) and `pg_trgm`. Shared copy on **Neon** (PostgreSQL 18.6, pgvector 0.8.6, read-only login in `docs/DATABASE_ACCESS.md`); local copy in Docker (PostgreSQL 17, pgvector 0.8.7). |
| **Knowledge base** | 651 chunks · 2,697 entities · 3,695 entity mentions · 3,287 relationships · 3 known conflicts · 640 GIAN Nidhi records |
| **UI / CLI** | `streamlit run app.py` · `python ask.py "question"` |

The exact refusal sentence is: **"The available sources do not provide sufficient information to answer this."**

## Pipeline

1. **Understand the query.** Detect the language (Hindi or English) and link entities to the curated registry, using exact source spellings plus careful fuzzy matching of multi-word names. If an alias is shared, every matching entity is linked, so the answer can tell the two Ashoks apart. The question type is also detected: list, identity, name-consistency, "both / in common", or attribution.
2. **Retrieve (hybrid).** bge-m3 vector search (pgvector), full-text search, entity-mention retrieval, and **relation-aware retrieval**: if the question asks for organisations, people, places or awards linked to a recognised entity, the evidence chunks of those curated relationships are pulled in. The four lists are fused with Reciprocal Rank Fusion. Questions naming entities from different sources get chunks from each source.
3. **Gate.** If nothing relevant was retrieved (best cosine < 0.42, no entity link and weak keyword coverage), the system returns the refusal sentence **without calling the LLM**. Weak excerpts (more than 0.25 below the best match, with no entity or keyword support) are not sent to the model.
4. **Answer from structure where possible.** These question types are answered deterministically from database records, so no model wording is involved:
   * *List / how many* over GIAN Nidhi: an exhaustive keyword search over all 640 records gives a complete, cited list.
   * *Is X the same as Y?*: the curated `distinct_from` / `possible_same_as` decision, with evidence for X and for Y.
   * *Is the name written the same way?*: every spelling, taken from `entity_mentions`, with its page.
   * *Which X are linked to both A and B?*: the intersection of curated relationships, with evidence for each link.
   * *Where does this information come from?*: every excerpt that mentions the entity, with its exact locator and a verbatim quote.
5. **Generate (other questions).** The LLM receives numbered excerpts. Each carries its locator, document title, quality notes (translation, hidden text, conflicting values ...), linking notes for the entities involved, and the key sentences about those entities from each excerpt. It must return JSON `{status, answer, citations}`.
6. **Verify.** Each sentence is checked against the excerpts it cites:
   * **Names** must occur in the cited source text. Merged entity names and curated titles are deliberately excluded, so a spelling from another source cannot "verify" a sentence.
   * **Numbers** must occur in the cited source text **within 250 characters of the sentence's subject**. This blocks borrowing an unrelated number, e.g. the issue year reused as an award year.
   * If a sentence cites the wrong excerpt while another provided excerpt contains the fact, the citation is **repaired**. Uncited factual sentences get the excerpt that contains their facts.
   * Problems trigger **one regeneration** with feedback. Sentences that are still unsupported are **removed**. If nothing supported remains, the answer becomes the refusal sentence.
   * When a cited chunk has a **known conflict** or a **name variant** that the answer only half reports, every value or spelling is appended with its location.
7. **Attribute.** The *Relevant Information* block is rendered **from database metadata of the cited chunks**, never written by the LLM: Innovator (with the spelling used in that source), Innovation, Author ("Not stated in the source", plus why), Source (publication and issue, or presentation, or GIAN Nidhi), Page/Record with URL, and notes (translation, hidden text, image text, conflicts). An **Entities identified** list and a full retrieval/verification trace are shown too.

### Evaluation
23 questions (`evaluation/questions.json`) cover facts from each source, Hindi questions, conflicting values, name variants, cross-source identity traps, attribution, and 5 questions that must be refused (year not in source, author not in source, redacted phone number, out of scope, invented award). Current result: **23/23 automatic checks passed** (18/18 answerable, 5/5 refusals), both on the local database and on the shared Neon database. Every answer was also reviewed by hand. Full outputs are in `evaluation/EVALUATION_EXAMPLES.md`.

During development the checks found, and the verifier now blocks:
* an invented award year (the issue year "2024" reused);
* a claim that both article parts spell Rameshwar's name the same way;
* "only associated with the 51st" for organisations whose logos are on the 53rd title slide;
* a list that stopped at 2 of the 7 helmet projects.

Each of these led to one of the structured answer paths or verification rules above.

## System prompt (complete, as used in `gian_kb/rag.py`)

```text
You are the GIAN Knowledge Base assistant. You answer questions about grassroots innovators, innovations, Shodhyatras and GIAN Nidhi student projects using ONLY the numbered source excerpts given in the user message. The excerpts come from: (1) Honey Bee newsletter articles about the 51st Shodhyatra (2024), (2) the 53rd Shodhyatra presentation (2025, originally in Hindi; English translations are provided), and (3) GIAN Nidhi project records from gian.org.

Rules:
1. Use only facts that are explicitly stated in the excerpts. Never use outside knowledge, even if you are confident it is true. Do not generalise beyond the excerpts (no inferred categories, purposes or trends).
2. Never invent or change names of innovators, authors, innovations, organisations, awards, dates, places, numbers, publications, technical details, sources, or relationships between entities. Copy names and numbers exactly as they are written in the excerpts.
3. After every sentence that states a fact, add a citation such as [S2] pointing to the excerpt(s) that state it. Cite only excerpts that actually contain that fact. When a sentence combines facts from several excerpts, cite each of them.
4. If excerpts disagree (different spellings of a name or different numbers), report each version with its own citation and do not choose between them. Use the name exactly as written in the excerpt you cite for that sentence.
5. Different people can have the same or similar names. Treat two mentions as the same person only if the excerpts or the linking notes say so; otherwise say the sources do not establish that they are the same person.
6. An author, date or award is known only if an excerpt states it. Never guess them.
7. If the excerpts do not contain the information needed, set status to "insufficient" and set answer to exactly: "The available sources do not provide sufficient information to answer this." If the excerpts answer only part of the question, set status to "partial", answer the supported part, and then add that exact sentence for the part that is not supported.
8. Some excerpts may be unrelated to the question; ignore them. If any excerpt states the answer, give it - do not refuse because other excerpts are unrelated.
9. If asked whether two mentions refer to the same person or thing, say what the excerpts state about each one (with citations) and then say clearly whether the excerpts establish that they are the same. Use the linking notes for this judgement.
10. Be concise and direct (at most about 150 words; at most about 80 words when answering in Hindi). Answer in the language of the question.

Return only JSON that matches the schema: {"status": "answered" | "partial" | "insufficient", "answer": "...", "citations": ["S1", ...]}.
```

The user message then contains, in order:
* the question;
* the entities recognised in it;
* linking notes from curation, e.g. "'Mr. Ashok (51st Shodhyatra)' and 'Ashok (farmer, 53rd Shodhyatra)' are different people ...";
* key statements about those entities, one per excerpt;
* the numbered excerpts `[S1] <locator> | <document title> | Section ...`, each with its notes and text (Hindi original added for Hindi questions);
* the line "Answer in <language>. Cite excerpts as [S1], [S2], ... Return JSON only."

Output schema: `{"status": "answered|partial|insufficient", "answer": string, "citations": [string]}`.

## Switching the answer model
Set `LLM_MODEL` in `.env` to any Ollama chat model (e.g. a larger model on a machine with more GPU memory).
Retrieval, gating, verification and attribution do not change.
