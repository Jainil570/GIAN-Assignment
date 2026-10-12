-- =====================================================================================
-- GIAN knowledge base - PostgreSQL + pgvector schema
-- Embedding model: BAAI/bge-m3 (via Ollama "bge-m3"), 1024 dimensions, cosine distance
-- =====================================================================================
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DROP VIEW IF EXISTS v_chunk_citations CASCADE;
DROP TABLE IF EXISTS eval_queries, data_quality_issues, known_conflicts, relationships, entity_mentions, entities,
                     chunks, gian_nidhi_projects, gian_nidhi_institutions, documents CASCADE;

-- One row per logical source document (PDF 2 holds two newsletter articles -> two rows)
CREATE TABLE documents (
    document_id        text PRIMARY KEY,
    source             text NOT NULL,
    source_type        text NOT NULL,          -- pdf_presentation | pdf_newsletter_article | web_table
    source_url         text NOT NULL,          -- Google Drive link / gian.org URL
    source_file        text,
    document_title     text NOT NULL,
    document_title_en  text,
    author             text,                   -- NULL = not stated in the source (never guessed)
    author_note        text,
    publication_name   text,
    publication_issue  text,
    publication_year   int,
    date_note          text,
    language           text,
    organisations      text[],
    organisation_note  text,
    event_id           text,
    locator_unit       text,                   -- page | slide | record
    extra              jsonb
);

-- Retrieval units. Every chunk repeats the provenance fields so a single row answers
-- "where did this come from?" without joins.
CREATE TABLE chunks (
    chunk_id           text PRIMARY KEY,
    document_id        text NOT NULL REFERENCES documents(document_id),
    data_category      text NOT NULL,          -- shodhyatra_report | shodhyatra_presentation | student_project | web_page_context
    content_type       text NOT NULL,          -- narrative | image_text | slide_unit | record | web_page_context
    language           text NOT NULL,          -- en | hi+en
    title              text,
    section            text,
    source             text NOT NULL,
    source_url         text NOT NULL,
    document_title     text NOT NULL,
    author             text,
    publication_name   text,
    publication_issue  text,
    publication_year   int,
    event_id           text,
    locator_type       text NOT NULL,          -- page | slide | record
    printed_pages      int[],                  -- newsletter page numbers as printed
    pdf_pages          int[],                  -- page index inside the PDF file
    slides             int[],
    record_ids         int[],                  -- GIAN Nidhi record IDs (identical duplicates folded in)
    locator            text,                   -- human-readable: 'Honey Bee Vol 35 (3) ..., p. 14' / 'slides 48-49' / 'record 37'
    innovator_names    text[],
    innovation_names   text[],
    persons            text[],
    organisations      text[],
    places             text[],
    awards             text[],
    events             text[],
    other_entities     text[],
    entity_ids         text[],
    text               text NOT NULL,          -- display text (English; translation for Hindi slides)
    text_original      text NOT NULL,          -- verbatim source text (Hindi for the 53rd deck)
    text_en            text,
    image_text         text,                   -- text transcribed from images (flagged)
    embedding_text     text NOT NULL,          -- exactly what was embedded
    extraction_method  text,
    translation        jsonb,
    quality_flags      text[],
    conflict_ids       text[],                 -- known_conflicts touching this chunk
    pii_redacted       boolean DEFAULT false,
    curation_notes     text,
    retrieved_at       timestamptz,
    metadata           jsonb NOT NULL,         -- full metadata record
    content_hash       text NOT NULL,
    pipeline_version   text,
    embedding_model    text NOT NULL,
    embedding          vector(1024) NOT NULL,
    tsv_simple         tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(title, '') || ' ' || embedding_text)) STORED,
    tsv_english        tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(text_en, text))) STORED
);

CREATE TABLE entities (
    entity_id    text PRIMARY KEY,
    type         text NOT NULL,                -- person | organisation | institution | place | innovation | practice | event | award | project ...
    name         text NOT NULL,
    aliases      text[] NOT NULL,              -- exact surface forms found in the sources
    documents    text[] NOT NULL,              -- documents where the entity is attested
    description  text,                         -- restates the sources only
    roles        text[],
    flags        text[],
    link_note    text,                         -- why spellings were (not) linked
    attributes   jsonb
);

CREATE TABLE entity_mentions (
    chunk_id     text REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    entity_id    text REFERENCES entities(entity_id) ON DELETE CASCADE,
    surface_form text,
    method       text,                         -- alias_match | curated | structured_field
    PRIMARY KEY (chunk_id, entity_id)
);

CREATE TABLE relationships (
    rel_id             text PRIMARY KEY,
    subject_id         text REFERENCES entities(entity_id),
    predicate          text NOT NULL,
    object_id          text REFERENCES entities(entity_id),
    status             text NOT NULL CHECK (status IN ('stated', 'probable', 'unverified', 'distinct')),
    evidence_chunk_ids text[] NOT NULL,
    evidence_locators  jsonb,
    note               text
);

-- Facts stated with different values in the sources (kept, never resolved)
CREATE TABLE known_conflicts (
    conflict_id  text PRIMARY KEY,
    attribute    text NOT NULL,
    entity_ids   text[] NOT NULL,
    keywords     text[],
    values       jsonb NOT NULL,                -- [{value, where, doc, page|slide, chunk_ids}]
    chunk_ids    text[] NOT NULL,
    note         text
);

CREATE TABLE gian_nidhi_institutions (
    institution_id        text PRIMARY KEY,
    canonical_name        text NOT NULL,
    match_keys            text,
    record_count          int,
    name_variants         text,
    possible_same_as      text,
    reviewed_not_same_as  text
);

CREATE TABLE gian_nidhi_projects (
    record_id             int PRIMARY KEY,
    sr_no                 int,
    project_name          text,
    participants          text[],
    participant_count     int,
    abstract              text,
    abstract_word_count   int,
    institution_name      text,
    institution_canonical text,
    institution_id        text REFERENCES gian_nidhi_institutions(institution_id),
    record_status         text,
    duplicate_group_id    text,
    duplicate_status      text,
    duplicate_of          int,
    data_quality_flags    text[],
    participants_raw      text,
    institution_raw       text,
    source                text,
    source_url            text,
    retrieved_at          timestamptz,
    chunk_id              text REFERENCES chunks(chunk_id)
);

CREATE TABLE data_quality_issues (
    issue_id      serial PRIMARY KEY,
    source        text,
    location      text,
    field         text,
    issue         text,
    action        text,
    value_before  text,
    value_after   text
);

-- Pre-computed bge-m3 embeddings for the evaluation questions, so vector search can be
-- tried in pure SQL without running any model.
CREATE TABLE eval_queries (
    query_id           text PRIMARY KEY,
    query_text         text NOT NULL,
    expected_behaviour text,
    embedding          vector(1024) NOT NULL
);

-- Indexes
CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX chunks_tsv_simple ON chunks USING gin (tsv_simple);
CREATE INDEX chunks_tsv_english ON chunks USING gin (tsv_english);
CREATE INDEX chunks_metadata ON chunks USING gin (metadata jsonb_path_ops);
CREATE INDEX chunks_document ON chunks (document_id);
CREATE INDEX chunks_entity_ids ON chunks USING gin (entity_ids);
CREATE INDEX entities_name_trgm ON entities USING gin (name gin_trgm_ops);
CREATE INDEX entity_mentions_entity ON entity_mentions (entity_id);
CREATE INDEX relationships_subject ON relationships (subject_id);
CREATE INDEX relationships_object ON relationships (object_id);
CREATE INDEX gn_projects_institution ON gian_nidhi_projects (institution_id);

-- Human-readable citation for every chunk
CREATE VIEW v_chunk_citations AS
SELECT c.chunk_id,
       c.document_id,
       c.source,
       c.document_title,
       coalesce(c.author, 'not stated in source') AS author,
       c.publication_name,
       c.publication_issue,
       c.publication_year,
       c.locator,
       c.source_url,
       c.innovator_names,
       c.innovation_names,
       c.quality_flags
FROM chunks c;

-- Vector search helper: SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id='Q01'), 5);
CREATE OR REPLACE FUNCTION match_chunks(query_embedding vector(1024), match_count int DEFAULT 8,
                                        filter_document text DEFAULT NULL)
RETURNS TABLE (chunk_id text, similarity double precision, document_id text, locator text, title text,
               source_url text, innovator_names text[], innovation_names text[], text text)
LANGUAGE sql STABLE AS $$
    SELECT c.chunk_id, 1 - (c.embedding <=> query_embedding) AS similarity, c.document_id, c.locator, c.title,
           c.source_url, c.innovator_names, c.innovation_names, c.text
    FROM chunks c
    WHERE filter_document IS NULL OR c.document_id = filter_document
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Keyword search helper (works for English and Hindi tokens): SELECT * FROM keyword_chunks('Noorjahan mango', 5);
CREATE OR REPLACE FUNCTION keyword_chunks(q text, match_count int DEFAULT 8)
RETURNS TABLE (chunk_id text, rank real, locator text, title text, text text)
LANGUAGE sql STABLE AS $$
    SELECT c.chunk_id,
           greatest(ts_rank(c.tsv_english, websearch_to_tsquery('english', q)),
                    ts_rank(c.tsv_simple, websearch_to_tsquery('simple', q))) AS rank,
           c.locator, c.title, c.text
    FROM chunks c
    WHERE c.tsv_english @@ websearch_to_tsquery('english', q) OR c.tsv_simple @@ websearch_to_tsquery('simple', q)
    ORDER BY rank DESC
    LIMIT match_count;
$$;

-- Everything the KB knows about an entity, with evidence: SELECT * FROM entity_profile('PER-SUNDARAM-VERMA');
CREATE OR REPLACE FUNCTION entity_profile(eid text)
RETURNS TABLE (relation text, other_entity text, status text, evidence_chunks text[], note text)
LANGUAGE sql STABLE AS $$
    SELECT r.predicate, o.name, r.status, r.evidence_chunk_ids, r.note
    FROM relationships r JOIN entities o ON o.entity_id = r.object_id WHERE r.subject_id = eid
    UNION ALL
    SELECT 'inverse:' || r.predicate, s.name, r.status, r.evidence_chunk_ids, r.note
    FROM relationships r JOIN entities s ON s.entity_id = r.subject_id WHERE r.object_id = eid;
$$;
