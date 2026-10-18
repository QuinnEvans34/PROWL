"""Two retained-draft readability regressions, no generation/retrieval replay."""
import json
from pathlib import Path
from time import monotonic
from retrieval.compare_development_rankings import pin,write
from src.retrieval.natural_answer import api,INSTRUCT_MODEL,INSTRUCT_MODEL_SHA
from src.retrieval.readable_render import render_and_check
ROOT=Path(__file__).resolve().parents[2]


def main():
 out=ROOT/'outputs/prowl/readable-render-v19-20261018';out.mkdir(exist_ok=False)
 paths=['docs/capstone/retrieval/READABLE-RENDER-V19-PLAN-2026-10-18.md','scripts/retrieval/check_readable_render.py','scripts/retrieval/supervise_readable_render.py','src/retrieval/readable_render.py','src/retrieval/qualified_answer.py','src/retrieval/natural_answer.py','outputs/prowl/section-answers-v17-20261018/quality-01.json','outputs/prowl/section-answers-v18-20261018/quality-03.json']
 receipt=dict(state='started',pins=[pin(p) for p in paths],outcomes=[]);write(out/'receipt.json',receipt)
 for p in paths[-2:]:
  old=json.loads((ROOT/p).read_text());question=old['request']['question'];a=old['response']['answer'];trace=[]
  raw=dict(claims=[dict(text=c['text'],citations=[dict(source=f"P{x['rank']}") for x in c['citations']]) for c in a['claims']])
  sources=[dict(source=f"P{e['rank']}",text=e['record']['text'],title=e['record']['citation']['title']) for e in old['response']['evidence']]
  start=monotonic();deadline=start+60
  assert any(m['name']==INSTRUCT_MODEL and m['digest']==INSTRUCT_MODEL_SHA for m in api('tags',port=11435,deadline=deadline)['models'])
  def call(path,payload=None):
   response=api(path,payload,port=11435,deadline=deadline);trace.append(dict(path=path,payload=payload,response=response));write(out/(old['id']+'-trace.json'),trace);return response
  try:
   result=render_and_check(question,raw,sources,call);status='completed'
  except Exception as e:result=dict(failure_type=type(e).__name__,reason=str(e));status='failed'
  write(out/(old['id']+'.json'),dict(question=question,original=old,result=result,seconds=monotonic()-start))
  receipt['outcomes'].append(dict(id=old['id'],state=status,seconds=monotonic()-start));write(out/'receipt.json',receipt);print(receipt['outcomes'][-1],flush=True)
 receipt['state']='completed';write(out/'receipt.json',receipt)

if __name__=='__main__':main()
