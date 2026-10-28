"""Explain and compare exact/HNSW plans only in the dedicated internal experiment DB."""
import json,sys,time,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from retrieval.direct_corpus import read_config,connect,encoder
from src.retrieval.direct_ingestion import vector_sql
from scripts.retrieval.benchmark_expert_speed_v1 import QUESTIONS

def main():
 out=ROOT/'outputs/prowl/expert-speed-20261028/index-forced-probe.json'
 if out.exists():raise ValueError('Preserve existing probe')
 c=dict(read_config(ROOT/'infra/retrieval/.env.ingestion.json'),port=55434);enc=encoder(c)
 import torch
 torch.set_num_threads(2)
 qs=[vector_sql(enc.encode([q])[0]) for q in QUESTIONS];rows=[]
 with connect(c) as db:
  db.execute('ANALYZE literature.passages')
  sql='SELECT passage_id FROM literature.passages WHERE collection_id=%s ORDER BY embedding <=> %s::vector LIMIT 5'
  exact=[]
  for q in qs:exact.append([r[0] for r in db.execute(sql,('research-disease-v1',q)).fetchall()])
  db.execute('CREATE INDEX speed_probe_hnsw ON literature.passages USING hnsw (embedding vector_cosine_ops)')
  db.execute('SET enable_seqscan=off');db.execute('SET enable_bitmapscan=off');db.execute('SET enable_sort=off')
  for q,ids in zip(qs,exact):
   t=time.monotonic();got=[r[0] for r in db.execute(sql,('research-disease-v1',q)).fetchall()];elapsed=time.monotonic()-t
   plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql,('research-disease-v1',q)).fetchone()[0]
   rows.append(dict(seconds=elapsed,recall_at_5=len(set(got)&set(ids))/5,hnsw_used='speed_probe_hnsw' in json.dumps(plan),plan=plan))
  db.execute('DROP INDEX literature.speed_probe_hnsw')
 out.write_text(json.dumps(dict(rows=rows,median_seconds=statistics.median(x['seconds'] for x in rows),all_used=all(x['hnsw_used'] for x in rows)),indent=2));print(out.read_text()[:300])
if __name__=='__main__':main()
