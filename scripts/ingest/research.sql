-- Local private catalog only. Counts refer to representations, not verified cases.
-- Run: sqlite3 -readonly data/private/inventory/2026-11-13-v4/catalog.sqlite < scripts/ingest/research.sql
.headers on
.mode column
SELECT dataset,split,role,subset,status,member_count,json_count,parsed_count
FROM archives ORDER BY dataset,split,role,subset;

-- Label categories are kept distinct; no implicit relabeling of source taxonomy.
SELECT a.split,a.subset,d.category,count(*) AS records
FROM documents d JOIN archives a USING(archive_id)
WHERE a.role='label' GROUP BY 1,2,3 ORDER BY 1,2,3;

SELECT a.role,count(*) AS representation_rows,count(DISTINCT d.source_key) AS distinct_source_keys
FROM documents d JOIN archives a USING(archive_id) GROUP BY a.role;

SELECT status,count(*) AS source_label_edges FROM pairing_candidates GROUP BY status;
SELECT code,sum(count) AS observations FROM issues GROUP BY code;

-- Explicit project investigation population. Not verified defendant comparisons.
SELECT d.source_id,a.split,d.source_key,d.case_no,d.court,d.decision_date,d.category,
       d.origin_reference_section_count,d.source_legal_verification
FROM documents d JOIN archives a USING(archive_id)
WHERE a.role='label' AND a.subset='general' AND d.category IN ('형사','형사A','형사B')
ORDER BY a.split,d.source_id LIMIT 20;

-- Compare taxonomy as supplied, without overwriting source or label categories.
SELECT a.role,d.category,count(*) AS records FROM documents d
JOIN archives a USING(archive_id) GROUP BY 1,2 ORDER BY 1,2;
SELECT role,count(*) AS duplicate_identifier_groups FROM (
  SELECT a.role,d.source_key FROM documents d JOIN archives a USING(archive_id)
  GROUP BY a.role,d.source_key HAVING count(*)>1
) GROUP BY role;
SELECT count(*) AS section_rows,sum(declared_char_count<>codepoint_length) AS declared_length_differs
FROM sections;
SELECT substr(d.decision_date,1,4) AS supplied_year,count(*) AS records
FROM documents d JOIN archives a USING(archive_id)
WHERE a.role='label' AND substr(d.decision_date,1,4)>'2026' GROUP BY 1;
