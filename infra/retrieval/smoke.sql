\set ON_ERROR_STOP on
SET statement_timeout = '30s';
CREATE EXTENSION IF NOT EXISTS vector;
BEGIN;
CREATE SCHEMA prowl_smoke;
CREATE TABLE prowl_smoke.passages (
  id integer PRIMARY KEY,
  build text NOT NULL,
  permitted boolean NOT NULL,
  body text NOT NULL,
  embedding vector(3) NOT NULL,
  terms tsvector GENERATED ALWAYS AS (to_tsvector('english', body)) STORED
);
INSERT INTO prowl_smoke.passages
SELECT g, CASE WHEN g <= 900 THEN 'published' ELSE 'staged' END,
       g % 10 <> 0, 'synthetic pancreas imaging passage ' || g,
       ARRAY[1.0, g / 1000.0, 0.0]::vector
FROM generate_series(1,1000) g;
-- Strongest vector match is forbidden: it must never escape the eligible view.
INSERT INTO prowl_smoke.passages VALUES
(1001, 'published', false, 'synthetic pancreas poison', '[1,0,0]');
CREATE VIEW prowl_smoke.eligible AS
SELECT * FROM prowl_smoke.passages WHERE build = 'published' AND permitted;
DO $$
DECLARE first_id integer; n integer;
BEGIN
  SELECT count(*) INTO n FROM prowl_smoke.eligible;
  IF n <> 810 THEN RAISE EXCEPTION 'eligibility count mismatch: %', n; END IF;
  SELECT id INTO first_id FROM prowl_smoke.eligible
    ORDER BY embedding <=> '[1,0,0]'::vector, id LIMIT 1;
  IF first_id <> 1 THEN RAISE EXCEPTION 'exact search/filter failed'; END IF;
  SELECT count(*) INTO n FROM prowl_smoke.eligible
    WHERE terms @@ plainto_tsquery('english', 'pancreas');
  IF n <> 810 THEN RAISE EXCEPTION 'lexical search failed'; END IF;
  IF EXISTS (SELECT 1 FROM prowl_smoke.eligible WHERE terms @@ plainto_tsquery('english','absentword'))
    THEN RAISE EXCEPTION 'empty search failed'; END IF;
  BEGIN
    INSERT INTO prowl_smoke.passages(id,build,permitted,body,embedding)
      VALUES (1,'published',true,'duplicate','[1,0,0]');
    RAISE EXCEPTION 'duplicate admitted';
  EXCEPTION WHEN unique_violation THEN NULL; END;
  BEGIN
    INSERT INTO prowl_smoke.passages(id,build,permitted,body,embedding)
      VALUES (1002,'published',true,'wrong dimensions','[1,0]');
    RAISE EXCEPTION 'wrong dimensions admitted';
  EXCEPTION WHEN data_exception THEN NULL; END;
END $$;
-- Same eligibility source in both branches; deterministic reciprocal rank fusion.
CREATE TABLE prowl_smoke.hybrid_result AS
WITH dense AS (
 SELECT id, row_number() OVER (ORDER BY embedding <=> '[1,0,0]'::vector,id) AS r
 FROM prowl_smoke.eligible ORDER BY embedding <=> '[1,0,0]'::vector,id LIMIT 10
), lexical AS (
 SELECT id, row_number() OVER (ORDER BY ts_rank_cd(terms,plainto_tsquery('english','pancreas')) DESC,id) AS r
 FROM prowl_smoke.eligible WHERE terms @@ plainto_tsquery('english','pancreas')
 ORDER BY ts_rank_cd(terms,plainto_tsquery('english','pancreas')) DESC,id LIMIT 10
)
SELECT id, sum(1.0/(60+r)) AS score
FROM (SELECT * FROM dense UNION ALL SELECT * FROM lexical) ranks
GROUP BY id ORDER BY score DESC,id LIMIT 10;
DO $$
BEGIN
 IF (SELECT id FROM prowl_smoke.hybrid_result ORDER BY score DESC,id LIMIT 1) <> 1
 OR (SELECT count(*) FROM prowl_smoke.hybrid_result) <> 10
 THEN RAISE EXCEPTION 'hybrid result mismatch'; END IF;
END $$;
COMMIT;
SELECT version();
SELECT extversion FROM pg_extension WHERE extname='vector';
SELECT * FROM prowl_smoke.hybrid_result ORDER BY score DESC,id;
SELECT 'synthetic_smoke_passed' AS result;
