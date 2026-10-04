# GIAN Knowledge Base: Data Analysis Report

**Scope:** two assignment PDFs and the GIAN Nidhi web table. The report covers how they were analysed, linked, cleaned and turned into a source-attributed, queryable knowledge base (PostgreSQL + pgvector).
**Pipeline version:** 1.0.0. **Data retrieved:** GIAN Nidhi on 2026-10-03 (UTC). **Everything is reproducible with** `python run_pipeline.py`.

---

## 1. Summary

| | 51st Shodhyatra (PDF 2) | 53rd Shodhyatra (PDF 1) | GIAN Nidhi (web) |
|---|---|---|---|
| What it is | 2 Honey Bee newsletter articles (Part I: Vol 35(3) pp. 13-15; Part II: Vol 35(4) pp. 2-4) | 94-slide presentation, Hindi, 04-10 June 2025 | Table of 640 ITI/Polytechnic student projects |
| Language / form | English, 3-column magazine layout | Hindi (Devanagari), slides with photos | English, 7 columns |
| Size | 6 PDF pages, 2,498 words | 82 slides with text, 12 image-only, 35k chars | 640 records (1,280 rows returned) |
| Author | not printed | not named (PDF metadata `Author='Admin'`) | not stated |
| Retrieval units | 14 section chunks + 2 image-text chunks | 56 "story units" (1-4 slides each) | 578 record chunks + 1 page-context chunk |

* **Knowledge base:** 651 chunks, all embedded with **BAAI/bge-m3 (1024-d)**.
* **Entities and links:** 2,697 entities, 240 of them curated by hand. They have 3,695 mentions and 3,287 typed relationships. 154 relationships are curated, each with a status: 141 *stated*, 7 *probable*, 2 *unverified*, 4 *distinct*.
* **Known conflicts:** 3 facts are stated with different values in the sources (`known_conflicts`).
* **Data-quality log:** 874 entries, one per change or flag.
* **Entities that appear in more than one source:** GIAN, SRISTI, Honey Bee Network, SRISTI Innovations, the Shodhyatra series, and the award "Padma Shri".
* **People:** no person, project or institution could be shown to appear in more than one source. One candidate (Dharamveer/Dharmveer) is recorded as **unverified**. Four look-alike name pairs are recorded as **distinct**.

---

## 2. Data structure analysis

### 2.1 PDF 2: 51st Shodhyatra (Honey Bee newsletter)
* **Two documents in one file.** PDF pages 1-3 are *"51st Shodhyatra: June 17 - 23, 2024, Harima-Chak Dhani | Rajasthan : Part-I"* (Honey Bee Vol 35 (3) July-September 2024, printed pp. 13-15). PDF pages 4-6 are *"The pain behind the glitter! 51 Shodhyatra ... Part-II"* (Vol 35 (4) October-December 2024, printed pp. 2-4). They were modelled as two documents (`SY51-HB-P1`, `SY51-HB-P2`) so each citation names the right issue and printed page.
* **Layout.** InDesign, three columns. Text blocks were classified by font, size and position into title, running header, standfirst, heading, body, caption, footer and footer question. Body text was put back into reading order. Paragraphs that continue across columns or pages, and across intervening photo captions, were re-joined (e.g. "...efforts of Shri" | "Himmat Ram Bhambhu..."). A URL split across two columns was re-joined.
* **Text only in images:** the *Shodhyatra route* signpost and a school alumni board. Both were transcribed and stored as separate `image_text` chunks.
* **Content:** 29 named people (innovators, healers, teachers, volunteers, centenarians), organisations, nine route stops, traditional knowledge (animal remedies, seed storage), innovations (one-litre tree planting, thornless Khejri) and ideas from an idea competition.

### 2.2 PDF 1: 53rd Shodhyatra presentation (Hindi)
* **Corrupted text layer.** The PDF was produced with PScript5/Distiller, and its Hindi font has an incomplete ToUnicode map. 1,303 glyph occurrences of 33 kinds come out as Latin letters (`è` for स्, `Ú` for ध्, `Ʌ` for ें, ...). The short-i matra (ि) and the reph (र्) come out in *visual* order (`िकया` instead of किया, `कायर्` instead of कार्य). A deterministic repair (`gian_kb/devanagari.py`) applies a glyph map, then i-matra reordering, then reph reordering. Every slide was checked against its rendered image: no residual glyphs remain, and only five stray-space fixes were needed.
* **Structure.** Title slide → map of Shodhyatras 1-52 → yatra statistics → five themed sections (Cultural, Technological & Traditional, Educational, Institutional, Social innovations) → profiles. A profile is usually a name slide followed by a description slide, so consecutive slides about the same subject were grouped into 56 curated *units*. Every sentence block keeps its slide number (`[Slide 48] ...`).
* **Images.** 12 slides have no text layer. The title slide and the map hold their text only in images, and newspaper clippings appear on slides 15, 17, 81, 83 and 84. Headlines and legible lines were transcribed (flag `visual_transcription`). Slides 26 and 94 are photos with no attributable content and are excluded.
* **Hidden text.** On slide 35, a paragraph about Bhuri Bai is drawn first and then covered by an image. It was detected from the PDF drawing order (`page.get_bboxlog`), kept, and flagged `hidden_text_in_pdf`.
* **Content:** 55 named people (artisans, farmers, teachers, students, social workers), community organisations, schools, crafts, crop varieties, machines and traditional foods.
* **Translation.** Each unit has a faithful English translation made during preprocessing (LLM-assisted, checked against the slides). The Hindi original stays the authoritative `text_original`. Both are embedded, so English and Hindi questions retrieve the same unit.

### 2.3 GIAN Nidhi (https://gian.org/gian-nidhi/)
* **How it was collected.** The page's HTML table is empty; the *WP Data Access* plugin fills it through a public DataTables AJAX call (`admin-ajax.php?action=wpda_datatables`). The scraper reads the nonce and publication id from the page, pages through every row, and stores the raw response (`data/raw/gian_nidhi/`).
* **Columns and meaning:**

| Source column | Meaning (observed) | KB field |
|---|---|---|
| ID | record id (1-640) | `record_id` |
| Column Status | always `active` | `record_status` |
| Sr No | always equal to ID | `sr_no` |
| Project Name | title | `project_name` |
| Participants | free-text team list | `participants` (list) and `participants_raw` |
| Abstracts | description | `abstract` |
| College Status | **the institution name, despite the label** | `institution_name` → `institution_canonical` / `institution_id` |

* **Missing fields:** no year, branch or discipline, guide, city or state, contact, or award.

---

## 3. Entities across sources (linking analysis)

Linking rule: **two mentions are the same entity only when the evidence goes beyond name similarity.** Valid evidence is the same unique innovation, place or role, or the same slide group. Every decision is stored as a relationship with a status and a note, and the RAG system reads these notes.

### 3.1 Entities confirmed in more than one source
| Entity | 51st (PDF 2) | 53rd (PDF 1) | GIAN Nidhi |
|---|---|---|---|
| **SRISTI** | "organized by SRISTI" (35(4) p.2); logo on route graphic | logo on title slide; "सृष्टि संस्था" colleagues (slide 60) | page footer: supports GIAN |
| **GIAN** | "supported by GIAN" (p.2); logo | logo on title slide (www.gian.org) | publisher of the repository |
| **Honey Bee Network** | supported the yatra (p.2); logo | logo; "हनी बी डेटाबेज" (slide 90) | page footer: supports GIAN |
| **SRISTI Innovations** | logo on route graphic | logo on title slide | - |
| **Shodhyatra series** | 51st event | 53rd event; map "Shodhyatra 1 to 52" | (site menu lists "Shodhyatra 1-53") |
| **Padma Shri** (award) | Sundaram Ji, Himmat Ram Bhambhu (no year) | Ramesh & Shanti Parmar (2023); Bhuri Bai (hidden text) | - |

### 3.2 Same name, *not* linked (would be wrong to merge)
| Pair | Decision | Why |
|---|---|---|
| "Dharamveer Khambojji" (51st, Kuchera; electric wheelchair, fruit juices) and "श्री धर्मवीर" (53rd, Yamunanagar; President's award; mahua machine) | **unverified** (`possible_same_as`) | Same first name and both are innovators on Shodhyatras, but the 53rd deck gives no surname, the 51st article gives no hometown or award, and the inventions differ. External verification is needed. |
| "Mr. Ashok" (51st, entrepreneur employing women) and "अशोक किसान" (53rd, farmer turned master trainer) | **distinct** | Different event, region and profile, even though both are linked to organic farming. |
| "Rinku Jeji" (51st idea) and "रिंकू राठवा" (53rd schoolgirl) | **distinct** | Different surname, event and region. |
| "Santosh Pachar" (carrot variety) and "संतोष बसोंड" (bamboo broom) | **distinct** | Different surname, event and work. |
| "Kamalji Bati" (temple operator) and "कमलजी / कलमसिंह डावर" (farmer) | **distinct** | Different surname, role and event. |
| "भाषा संस्था" (slide 39) and "भाषा केंद्र" (slide 70) | **unverified** | Possibly the same organisation; the deck does not say. |
| Ten different people surnamed *Rathwa* (53rd) | separate entities | A community surname is not evidence of identity. |
| "Presidential awardee" (Pachar) and "राष्ट्रपति पुरस्कार" (Dharmveer) | one generic award node, flagged | Neither the award name nor the year is given, so the node does **not** imply they received the same award. |

### 3.3 Spelling variants linked *within* a source (with evidence)
| Canonical entity | Variants in the sources | Status |
|---|---|---|
| Sundaram Verma | Shri Sundaram Ji / Sundaram Vermaji / Sunda Ram Verma | linked: the same unique "one litre of water" technique |
| Himmat Ram Bhambhu | ... Bhambhu / Bhambhuji / Himmat Ramji Bambhu / Himmatramji Bambhu | linked: same village, forest and conservation work |
| Rameshwar (thornless Khejri) | "Shri Rameshwar **Prasad** Ji" (Part I) / "Rameshwar **Lal** ji" (Part II) | **probable**; name conflict unresolved |
| Panchariya | "**Rahulchand**" (Part I) / "**Rawalchand**" (Part II) | **probable**; also a count conflict (8 vs 5 varieties) |
| Shivkumarji, Sandhya Kulkarni, Kalamsingh Dawar, Rajendra Shrivastav | शिवकुमरजी/शिवकुमारजी; संध्या/साध्यजी; कलमसिंह/कमलजी; श्रीवास्त/श्रीवास्तव (नीरज) | linked within the same slide or unit |
| Mehul Rathwa | "मेहुल राठवा" (slide 34) / "छात्र मेहुल" (slide 68) | **probable**: same first name and school (Gunata), same art activity |
| Places | छोटाउदेपुर / छोटा उदेपुर / छोटा उदयपुर / छोटा उदैपुर / छोटाउदयपुर; Likhmidas / Likhimdas; Chak Dhani / Chakdhanii | aliases of one place |

### 3.4 GIAN Nidhi and the Shodhyatras
No person, project or institution is shared. Overlaps are **topical only**: the 51st idea "scooter starts only when the helmet is worn" and three helmet projects; Dharamveer's electric wheelchair and wheelchair projects; welding machines; banana fibre. These are left to semantic search and **not** recorded as identity links. GIAN appears in both, as publisher of GIAN Nidhi and as supporter of the 51st Shodhyatra.

---

## 4. Data gaps

| Gap | Where | Effect / handling |
|---|---|---|
| No author / byline | all three sources | `author = NULL` plus `author_note`. The assistant answers "not stated" and never guesses. |
| Award years missing | Padma Shri of Sundaram Ji and Himmat Ram Bhambhu; Pachar and Dharmveer awards (name and year) | Questions about them are refused (tested, Q18). |
| Locations missing | PMC Girls School, Good Morning Club, Ashok (53rd), Archana Rathwa's village | stored as unknown |
| Innovator not named | mobile air pump (slide 56), toy-car children, paan-methi farmer, robot students, Khejri seed-storage practitioner | flag `innovator_not_named` |
| Missing units / unclear wording | "55 लंबा पिठोरा" (no unit); Bharti Soni slide ("कोट लिखर", "पेन्ट") | kept verbatim, marked `[unclear in source]` |
| Acronyms not expanded | ICCIG, TRC, PMC; NIF appears only as a URL | not expanded (expanding would be outside knowledge) |
| Cross-reference to a missing page | "(refer to p 23)" in Honey Bee 35(4) | noted; page not available |
| Text only in images | title slide, map, clippings, route graphic, alumni board | headlines and legible lines transcribed and flagged; personal names on the alumni board not transcribed |
| GIAN Nidhi missing values | 17 abstracts, 46 institutions, 9 participant lists, 10 placeholder titles ("not available") | flags per record |
| GIAN Nidhi missing structure | no year, branch, guide, location, institution code | see recommended fields |

---

## 5. Data-cleaning decisions

| # | Issue found | Decision | Rationale |
|---|---|---|---|
| 1 | Endpoint returned every GIAN Nidhi row twice (1,280 rows, 640 IDs, identical content) | drop exact duplicate rows | technical duplication, nothing lost |
| 2 | Same project title under different IDs (157 title groups) | link as duplicates **only** when the team also matches (≥75% overlap): 62 *exact* copies, 87 *probable* (content differs). 58 records that share a title with a *different team* stay separate. Nothing is deleted. | a shared title alone is not the same project (e.g. two different "SMART HELMET" teams) |
| 3 | Abstract stored in the "College Status" column (10 records) | moved to `abstract`; institution set to unknown | column shift; the institution is truly unknown |
| 4 | HTML entities (277), mojibake (`WomenÃƒÂ¢â€šÂ¬...`) (56 values), non-breaking spaces, `<br>` | normalised with `ftfy` and `html.unescape`; raw values kept | readability and matching; auditable |
| 5 | 300 raw institution strings | deterministic key (abbreviations expanded, punctuation and case removed), then a **manual review** of fuzzy look-alikes → 159 institutions. Same name + same city → merged. Different city (Arvi≠Amravati, Jalna≠Jalgaon) → kept apart. Ambiguous (Y.B. vs D.Y. Patil, Bhavubhai vs Bhagubhai, acronym vs full name) → kept apart, flagged `possible_same_as` | avoid false merges of similar names |
| 6 | Participants as free text (`"Satyanarayana, B. and Prof. Sastry, L."`) | split on `, ; / and &`; initial-only parts re-attached; honorifics ignored for matching; ambiguous splits flagged (24) | list field for linking; raw text kept |
| 7 | GIAN Nidhi person identity | the same name is merged only **within the same institution** | same name at different colleges can be different people |
| 8 | Broken Devanagari in PDF 1 | deterministic repair plus review against slide images; 5 documented spacing fixes | exact, reproducible Hindi text |
| 9 | Hidden text (slide 35) | kept, flagged `hidden_text_in_pdf`; answers say it is not visible on the slide | it is in the document, but readers cannot see it |
| 10 | Leftover chatbot sentence on slide 54 ("अगर आप इसे और संक्षिप्त रूप में चाहते हैं, तो यह रहा") | kept verbatim, flagged `editorial_artifact` | source fidelity; the flag stops it being used as content |
| 11 | Phone numbers (slides 15, 37 and banner) | **redacted** in all KB text (`[फ़ोन नंबर हटाया गया]`) | personal data has no place in a shared KB |
| 12 | Conflicting values (mango weight 2-4 / 2-4.5 / 3-4 kg; 8 vs 5 sweet-potato varieties; 123 vs 118 km cycled) | all values kept with locators in `known_conflicts`; answers must report each value | never pick a value silently |
| 13 | Name spelling conflicts | one entity with all surface forms as aliases; per-chunk surface form in `entity_mentions`; status *probable* where the name itself conflicts | attribution shows the name as written in each source |
| 14 | Footer questions, running headers, page numbers | removed from content, used as provenance (issue, printed page) | boilerplate is noise for retrieval |
| 15 | Historical claims on slides 92-93 (some unusual) | stored as printed, flagged `unverified_historical_claims` | not corrected from outside knowledge |
| 16 | Inconsistent gender marking (slide 65: "श्री" with a feminine verb) | gender not inferred; flagged | avoid assumptions |
| 17 | Margin inconsistency (buy Rs 5, sell Rs 13, stated average margin Rs 7; costs stated separately) | kept as stated; mentioned only in this report | the difference is our arithmetic, not a stated value |

All record-level actions are in `data/processed/data_quality_issues.csv` (and the `data_quality_issues` table).

---

## 6. Recommended linking fields (for GIAN's own data)

1. **Stable identifiers.** `innovator_id` (one per person across HBN, NIF and GIAN systems), `innovation_id`, `shodhyatra_id` (number + season + year), `publication_id` (newsletter + volume/issue + page), `project_id` (GIAN Nidhi), and `institution_id`, ideally an official code such as AISHE or state DTE.
2. **Names.** Store given name, surname and honorific (Shri, Smt., Mr., ji) separately, the Devanagari spelling **and** a romanised spelling, plus an alias list. The variants in §3.3 would then not need manual linking.
3. **Places.** Village, tehsil, district and state as separate fields, with official LGD codes. Spelling variants (Chhota Udepur ×5) then become irrelevant.
4. **Awards.** Award name, awarding body and year as separate fields (not "a Presidential awardee").
5. **Event participation.** For every person met on a Shodhyatra: shodhyatra_id, date, village, role (innovator, healer, teacher, volunteer) and a page or slide reference.
6. **GIAN Nidhi.** Add year, branch or discipline, guide or faculty, institution code, city, district, state, and consent for contact details. Rename "College Status" to "Institution". Remove the duplicate imports (139 groups).
7. **Provenance on every record:** source document id, page or slide, URL, retrieval date, extraction method, translation flag. This KB already stores all of these on every chunk.

---

## 7. How the knowledge is structured for AI

* **Chunks** (`chunks` table). Each chunk is one retrieval unit carrying **all** provenance fields: source, URL, document title, author (or why it is unknown), publication and issue, year, printed and PDF page / slide / record ids, a human-readable locator, innovators, innovations, persons, organisations, places, awards, entity ids, quality flags and known conflicts. It stores the verbatim original text, an English translation for Hindi, transcribed image text, and the exact text that was embedded. Each embedded text starts with a header such as `[Source: Honey Bee Vol 35 (3)... | p. 14 | Section: ...]`.
* **Entities and mentions.** Each entity has every surface form as an alias, scoped to the documents where it occurs. A mention records the exact spelling used in that chunk.
* **Relationships.** Typed (`innovator_of`, `organised_by`, `logo_shown`, `route_includes`, `possible_same_as`, `distinct_from`, ...) with status and evidence chunk ids. This lets the system answer relationship questions from evidence, not from name similarity.
* **Known conflicts and the data-quality log.** Stored as tables, so uncertainty is explicit and queryable.

See `docs/DATABASE_ACCESS.md` for the schema and queries, and `docs/SYSTEM.md` for the retrieval and answer pipeline.

## 8. Limitations
* English translations of the Hindi slides are machine-assisted (reviewed). Hindi remains the authoritative text.
* Image text is partially transcribed (headlines and legible lines only).
* "Probable" and "unverified" links need confirmation by GIAN staff or the original records.
