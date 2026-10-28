"""Load verified frozen batches into the dedicated internal DB and compare exact retrieval."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from retrieval.direct_corpus import read_config,limits,connect,encoder
from src.retrieval.direct_ingestion import initialize,load_batch,vector_sql
from src.retrieval.development_set import checked_json
from src.retrieval.corpus_inventory import database_inventory

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--load',action='store_true');a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve existing report')
    c=read_config(ROOT/'infra/retrieval/.env.local-expert.json');limits(c)
    if c.get('storage')!='internal':raise ValueError('Internal profile required')
    spec=json.loads((ROOT/'configs/evidence/development-search-v1.json').read_text());manifest=checked_json(spec['manifest'],ROOT)
    with connect(c) as db:
        if a.load:
            initialize(db)
            for pin in manifest['batches']:load_batch(db,spec['collection'],checked_json(pin,ROOT))
        inventory=database_inventory(db,spec['collection'])
        if inventory!=manifest['inventory']:raise ValueError('Corpus inventory mismatch')
        size=db.execute('select pg_database_size(current_database())').fetchone()[0]
        if size>8*1024**3:raise ValueError('Database cap')
    import torch
    torch.set_num_threads(2);enc=encoder(c)
    assert next(enc.model.parameters()).device.type=='cpu'
    previous=json.loads((ROOT/'outputs/prowl/expert-speed-20261028/retrieval-benchmark.json').read_text())
    cases=[r for r in previous['rows'] if r['repeat']==0];results=[]
    with connect(c) as db:
        for row in cases:
            start=time.monotonic();q=vector_sql(enc.encode([row['question']])[0])
            ids=[r[0] for r in db.execute('SELECT passage_id FROM literature.passages WHERE collection_id=%s ORDER BY embedding <=> %s::vector,passage_id LIMIT 5',(spec['collection'],q)).fetchall()]
            results.append(dict(question=row['question'],ids=ids,matched=ids==row['ids'],seconds=time.monotonic()-start))
    report=dict(inventory=inventory,database_bytes=size,results=results,all_matched=all(r['matched'] for r in results),answer_model_calls=0)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(database_bytes=size,questions=len(results),all_matched=report['all_matched'])))
    if not report['all_matched']:raise SystemExit(1)
if __name__=='__main__':main()
