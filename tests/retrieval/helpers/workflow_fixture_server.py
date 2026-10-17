"""Synthetic browser-test server. Never loads an encoder, database or model."""
import argparse
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from serve_research_workflow import workflow_handler, LocalFixtureServer
from src.retrieval.research_workflow import ResearchWorkflow
from src.retrieval.direct_ingestion import source_bundle,source_passages,digest
from src.retrieval import grounded_answer as g
from src.retrieval.guided_research import QUESTIONS
from tests.retrieval.test_direct_ingestion import XML

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=8015)
a=p.parse_args();root=a.output/str(uuid4());root.mkdir(parents=True)
source=root/'synthetic.xml';source.write_text(XML)
row=list(source_passages(source_bundle(source)))[1]
selected=0
provenance=dict(model=g.MODEL,model_sha256=g.MODEL_SHA,policy=g.POLICY,prompt_sha256=digest(g.SYSTEM),fixture='synthetic-no-model')
def retrieve(_):return [dict(record=row,score=1.0)]
def generate(question,passages):
    global selected
    selected+=1
    time.sleep(1.2)  # Make the running selection observable by status polling.
    rejected=selected==1
    missing=question==next(q['label'] for q in QUESTIONS if q['id']=='eus')
    return dict(provenance=provenance,model_called=False,
        validation='generation_rejected' if rejected else 'exact_quotes_verified',
        answer=dict(status='insufficient_evidence' if rejected or missing else 'excerpts',extracts=[] if rejected or missing else [dict(passage_id=row['passage']['passage_id'],quote=row['text'])]))
store=ResearchWorkflow(root/'runs',retrieve,'research-v1','synthetic-encoder','synthetic-corpus',generate)
server=LocalFixtureServer(('127.0.0.1',a.port),workflow_handler(store))
print('SYNTHETIC WORKFLOW FIXTURE:',root,flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
