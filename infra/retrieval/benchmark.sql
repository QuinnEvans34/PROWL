\set ON_ERROR_STOP on
SET statement_timeout='10min';
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA benchmark;
CREATE TABLE benchmark.passages (
 id integer PRIMARY KEY, bucket integer NOT NULL, permitted boolean NOT NULL,
 body text NOT NULL, embedding vector(128) NOT NULL,
 terms tsvector GENERATED ALWAYS AS (to_tsvector('english',body)) STORED
);
INSERT INTO benchmark.passages(id,bucket,permitted,body,embedding)
SELECT g,g%100,g%10<>0,'synthetic pancreas imaging group '||(g%100),
 ARRAY(SELECT sin(g::double precision*d*d*.0001)::real FROM generate_series(1,128) d)::vector
FROM generate_series(1,100000) g;
CREATE INDEX passage_hnsw ON benchmark.passages USING hnsw(embedding vector_cosine_ops);
CREATE INDEX passage_fts ON benchmark.passages USING gin(terms);
ANALYZE benchmark.passages;
CREATE TABLE benchmark.measurements (
 query integer, scope text, eligible integer, exact_ids integer[], default_ids integer[],
 iterative_ids integer[], default_recall float, iterative_recall float,
 default_ms float, iterative_ms float, hybrid_exact_ms float
);
-- Independent synthetic queries; do not use the indexed vector itself as a query.
DO $$
DECLARE q vector(128); mode text; predicate text; exact_ids integer[]; default_ids integer[];
 iterative_ids integer[]; hybrid_ids integer[]; n integer; started timestamptz;
 default_ms float; iterative_ms float; hybrid_ms float; dr float; ir float;
BEGIN
FOR j IN 1..20 LOOP
 q := ARRAY(SELECT sin((100000+j)::double precision*d*d*.0001)::real FROM generate_series(1,128) d)::vector;
 FOREACH mode IN ARRAY ARRAY['broad','one_percent','fewer_than_k','empty'] LOOP
 predicate := CASE mode WHEN 'broad' THEN 'permitted'
 WHEN 'one_percent' THEN 'permitted AND bucket=7'
 WHEN 'fewer_than_k' THEN 'permitted AND id<=5'
 ELSE 'permitted AND bucket=0' END;
 EXECUTE 'SELECT count(*) FROM benchmark.passages WHERE '||predicate INTO n;
 PERFORM set_config('enable_indexscan','off',true);
 PERFORM set_config('enable_bitmapscan','off',true);
 PERFORM set_config('enable_seqscan','on',true);
 EXECUTE 'SELECT coalesce(array_agg(id),ARRAY[]::integer[]) FROM (SELECT id FROM benchmark.passages WHERE '||predicate||' ORDER BY embedding <=> $1,id LIMIT 10) a' INTO exact_ids USING q;
 PERFORM set_config('enable_indexscan','on',true);
 PERFORM set_config('enable_bitmapscan','on',true);
 PERFORM set_config('enable_seqscan','off',true);
 PERFORM set_config('hnsw.iterative_scan','off',true);
 started:=clock_timestamp();
 EXECUTE 'SELECT coalesce(array_agg(id),ARRAY[]::integer[]) FROM (SELECT id FROM benchmark.passages WHERE '||predicate||' ORDER BY embedding <=> $1 LIMIT 10) a' INTO default_ids USING q;
 default_ms:=extract(epoch FROM clock_timestamp()-started)*1000;
 PERFORM set_config('hnsw.iterative_scan','strict_order',true);
 started:=clock_timestamp();
 EXECUTE 'SELECT coalesce(array_agg(id),ARRAY[]::integer[]) FROM (SELECT id FROM benchmark.passages WHERE '||predicate||' ORDER BY embedding <=> $1 LIMIT 10) a' INTO iterative_ids USING q;
 iterative_ms:=extract(epoch FROM clock_timestamp()-started)*1000;
 -- Exact eligible fallback combined with lexical rank fusion: same scope in each branch.
 PERFORM set_config('enable_indexscan','off',true);
 PERFORM set_config('enable_bitmapscan','off',true);
 PERFORM set_config('enable_seqscan','on',true);
 started:=clock_timestamp();
 EXECUTE 'WITH dense AS (SELECT id,row_number() OVER (ORDER BY embedding <=> $1,id) r FROM benchmark.passages WHERE '||predicate||' ORDER BY embedding <=> $1,id LIMIT 10), lexical AS (SELECT id,row_number() OVER (ORDER BY ts_rank_cd(terms,plainto_tsquery(''english'',''pancreas'')) DESC,id) r FROM benchmark.passages WHERE '||predicate||' AND terms @@ plainto_tsquery(''english'',''pancreas'') ORDER BY ts_rank_cd(terms,plainto_tsquery(''english'',''pancreas'')) DESC,id LIMIT 10) SELECT array_agg(id) FROM (SELECT id,sum(1.0/(60+r)) score FROM (SELECT * FROM dense UNION ALL SELECT * FROM lexical) a GROUP BY id ORDER BY score DESC,id LIMIT 10) b' INTO hybrid_ids USING q;
 hybrid_ms:=extract(epoch FROM clock_timestamp()-started)*1000;
 IF coalesce(cardinality(hybrid_ids),0)<>least(10,n) THEN RAISE EXCEPTION 'hybrid count mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM unnest(default_ids||iterative_ids||coalesce(hybrid_ids,ARRAY[]::integer[])) x JOIN benchmark.passages p ON p.id=x WHERE NOT p.permitted) THEN RAISE EXCEPTION 'rights filter leaked'; END IF;
 SELECT CASE WHEN cardinality(exact_ids)=0 THEN 1 ELSE count(*)::float/cardinality(exact_ids) END INTO dr FROM unnest(default_ids) id WHERE id=ANY(exact_ids);
 SELECT CASE WHEN cardinality(exact_ids)=0 THEN 1 ELSE count(*)::float/cardinality(exact_ids) END INTO ir FROM unnest(iterative_ids) id WHERE id=ANY(exact_ids);
 INSERT INTO benchmark.measurements VALUES(j,mode,n,exact_ids,default_ids,iterative_ids,dr,ir,default_ms,iterative_ms,hybrid_ms);
 END LOOP;
END LOOP;
END $$;
SELECT scope,min(eligible),avg(default_recall),avg(iterative_recall),
 percentile_cont(.95) WITHIN GROUP(ORDER BY hybrid_exact_ms) hybrid_p95_ms
FROM benchmark.measurements GROUP BY scope ORDER BY scope;
