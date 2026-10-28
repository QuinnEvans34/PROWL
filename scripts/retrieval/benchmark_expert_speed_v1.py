"""Isolated internal-DB benchmark; CPU encoder only, no answer-model calls.
Requires the dedicated disposable port55434; never writes to the live database.
"""
import json,sys,time,statistics,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from retrieval.direct_corpus import read_config,connect,encoder
from src.retrieval.direct_ingestion import initialize,load_batch,vector_sql
from src.retrieval.development_set import checked_json
from src.retrieval.corpus_inventory import database_inventory

QUESTIONS=['What does the pancreas do?','How big is the pancreas?',
'What additional findings help distinguish inflammation from a pancreatic tumor?',
'How is pancreatic volume measured on MRI?','Can fat infiltration look like a pancreatic tumor?',
'What is the normal pancreatic stiffness range in kilopascals?',
'Where is the pancreas located?','What are the limitations of CT for small pancreatic tumors?']


def main():
    out=Path(sys.argv[1]);report=out/'retrieval-benchmark.json'
    if report.exists():raise ValueError('Preserve existing benchmark')
    spec=json.loads((ROOT/'configs/evidence/development-search-v1.json').read_text());manifest=checked_json(spec['manifest'],ROOT)
    batches=[checked_json(p,ROOT) for p in manifest['batches']]
    config=read_config(ROOT/'infra/retrieval/.env.ingestion.json');config=dict(config,port=55434)
    with connect(config) as db:
        initialize(db)
        for batch in batches:load_batch(db,spec['collection'],batch)
        assert database_inventory(db,spec['collection'])==manifest['inventory']
        size=db.execute('select pg_database_size(current_database())').fetchone()[0]
    t=time.monotonic();enc=encoder(config);load_seconds=time.monotonic()-t
    import torch
    torch.set_num_threads(2)
    assert next(enc.model.parameters()).device.type=='cpu'
    rows=[];queries=[];exact=[]
    sql='SELECT passage_id,embedding <=> %s::vector AS distance FROM literature.passages WHERE collection_id=%s ORDER BY embedding <=> %s::vector,passage_id LIMIT 5'
    for repeat in range(2):
        for question in QUESTIONS:
            t=time.monotonic();read_config(ROOT/'infra/retrieval/.env.ingestion.json');config_s=time.monotonic()-t
            t=time.monotonic();db=connect(config);connect_s=time.monotonic()-t
            with db:
                t=time.monotonic();assert database_inventory(db,spec['collection'])==manifest['inventory'];inventory_s=time.monotonic()-t
                t=time.monotonic();q=vector_sql(enc.encode([question])[0]);embedding_s=time.monotonic()-t
                t=time.monotonic();hits=db.execute(sql,(q,spec['collection'],q)).fetchall();query_s=time.monotonic()-t
                explain=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql,(q,spec['collection'],q)).fetchone()[0]
            rows.append(dict(question=question,repeat=repeat,config_seconds=config_s,connect_seconds=connect_s,inventory_seconds=inventory_s,embedding_seconds=embedding_s,query_seconds=query_s,total_seconds=config_s+connect_s+inventory_s+embedding_s+query_s,ids=[x[0] for x in hits],plan=explain))
            if repeat==0:queries.append(q);exact.append([x[0] for x in hits])
    ann=[]
    with connect(config) as db:
        t=time.monotonic();db.execute('CREATE INDEX speed_probe_hnsw ON literature.passages USING hnsw (embedding vector_cosine_ops)');build=time.monotonic()-t
        db.execute('SET enable_seqscan=off')
        for q,ids in zip(queries,exact):
            sql2='SELECT passage_id FROM literature.passages WHERE collection_id=%s ORDER BY embedding <=> %s::vector LIMIT 5'
            t=time.monotonic();hits=[r[0] for r in db.execute(sql2,(spec['collection'],q)).fetchall()];duration=time.monotonic()-t
            plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql2,(spec['collection'],q)).fetchone()[0]
            ann.append(dict(seconds=duration,recall_at_5=len(set(hits)&set(ids))/5,ids=hits,plan=plan))
        db.execute('DROP INDEX literature.speed_probe_hnsw')
    result=dict(scope='CPU retrieval on isolated internal storage; no concurrent external comparison due stale Docker mount; not answer latency',database_bytes=size,encoder_load_seconds=load_seconds,corpus_inventory=manifest['inventory'],rows=rows,ann=ann,hnsw_build_seconds=build,medians={key:statistics.median(r[key] for r in rows) for key in rows[0] if key.endswith('_seconds')},teacher_not_paused=True,answer_model_calls=0)
    report.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['rows','ann','corpus_inventory']}),flush=True)
if __name__=='__main__':main()
