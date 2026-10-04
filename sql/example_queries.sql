-- =====================================================================================
-- Example queries for the GIAN knowledge base (run with psql or any SQL client)
-- =====================================================================================

-- 0. What is in the database?
SELECT document_id, source, document_title, publication_issue, author, source_url FROM documents;
SELECT document_id, data_category, count(*) FROM chunks GROUP BY 1, 2 ORDER BY 1;

-- 1. Vector search WITHOUT running a model: use a pre-computed bge-m3 question embedding
SELECT query_id, query_text FROM eval_queries ORDER BY query_id;
SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id = 'Q01'), 5);   -- one-litre tree planting
SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id = 'Q10'), 3);   -- Hindi question

-- 2. Vector search restricted to one source document
SELECT * FROM match_chunks((SELECT embedding FROM eval_queries WHERE query_id = 'Q08'), 3, 'SY53-PPT');

-- 3. Raw pgvector operator (cosine distance <=>) with full attribution columns
SELECT c.chunk_id, round((1 - (c.embedding <=> q.embedding))::numeric, 3) AS similarity,
       c.locator, c.source_url, coalesce(c.author, 'not stated in source') AS author,
       c.innovator_names, c.innovation_names
FROM chunks c, (SELECT embedding FROM eval_queries WHERE query_id = 'Q07') q
ORDER BY c.embedding <=> q.embedding
LIMIT 5;

-- 4. Keyword search (English stemming + Hindi tokens)
SELECT * FROM keyword_chunks('thornless Khejri grafting', 5);
SELECT * FROM keyword_chunks('नूरजहां', 3);

-- 5. "Where did this information come from?" - every provenance field of a chunk
SELECT * FROM v_chunk_citations WHERE chunk_id = 'SY53-PPT-U26';
SELECT chunk_id, metadata->'translation' AS translation, metadata->'extraction_method' AS extraction,
       quality_flags, curation_notes
FROM chunks WHERE chunk_id = 'SY53-PPT-U26';

-- 6. Entities: aliases (spelling variants) and where each is mentioned
SELECT entity_id, type, name, aliases, link_note FROM entities WHERE entity_id = 'PER-PANCHARIYA';
SELECT m.chunk_id, m.surface_form, c.locator
FROM entity_mentions m JOIN chunks c USING (chunk_id) WHERE m.entity_id = 'PER-RAMESHWAR-KHEJRI';

-- 7. Relationships with evidence (graph view of one entity)
SELECT * FROM entity_profile('EVT-SY51');

-- 8. Cross-source entities (mentioned in more than one source document)
SELECT e.entity_id, e.name, array_agg(DISTINCT c.document_id) AS documents
FROM entities e JOIN entity_mentions m USING (entity_id) JOIN chunks c USING (chunk_id)
GROUP BY e.entity_id, e.name
HAVING count(DISTINCT CASE WHEN c.document_id LIKE 'SY51%' THEN 'SY51' ELSE c.document_id END) > 1;

-- 9. Identity decisions: links that are NOT established / explicitly distinct people
SELECT s.name AS subject, r.predicate, o.name AS object, r.status, r.note
FROM relationships r JOIN entities s ON s.entity_id = r.subject_id JOIN entities o ON o.entity_id = r.object_id
WHERE r.status IN ('unverified', 'distinct', 'probable') AND r.predicate IN ('possible_same_as', 'distinct_from', 'name_conflict');

-- 10. Known conflicts (facts stated with different values)
SELECT conflict_id, attribute, jsonb_path_query_array(values, '$[*].value') AS values FROM known_conflicts;

-- 11. GIAN Nidhi structured queries
SELECT institution_canonical, count(*) FROM gian_nidhi_projects
WHERE duplicate_status <> 'exact_duplicate' GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
SELECT record_id, project_name, participants, institution_canonical
FROM gian_nidhi_projects WHERE project_name ILIKE '%helmet%';
SELECT duplicate_group_id, array_agg(record_id ORDER BY record_id), min(project_name), array_agg(duplicate_status)
FROM gian_nidhi_projects WHERE duplicate_group_id IS NOT NULL GROUP BY 1 ORDER BY 1 LIMIT 10;

-- 12. Data-quality log
SELECT source, issue, count(*) FROM data_quality_issues GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 20;
