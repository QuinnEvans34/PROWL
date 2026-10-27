"""Isolated synthetic reviewer exercise. Never point at a live review root."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests'),str(ROOT/'scripts')]
from test_review_store import package
from test_case_literature_workflow_v1 import capture_fixture
from src.review.store import ReviewStore,encode,digest
from src.review.literature_attachments_v1 import LiteratureAttachments
from scripts.serve_reviews import create_app
from fastapi.responses import JSONResponse


def build(root,node):
    if not root.exists():
        root.mkdir(parents=True)
        source=package.__wrapped__(root)
        (root/'attachments').mkdir()
        (root/'capture.json').write_bytes(encode(capture_fixture()))
        (root/'synthetic-only.json').write_text('{"synthetic_only":true}')
    if json.loads((root/'synthetic-only.json').read_text())!={'synthetic_only':True}:raise ValueError('Synthetic root required')
    source=root/'source'
    store=ReviewStore(root/'records',source,floor_bytes=50_000_000_000)
    attachments=LiteratureAttachments(root/'attachments',store,node=node)
    app=create_app(store,port=8020,attachments=attachments)
    @app.get('/walkthrough-identity')
    def identity():
        raw=(source/'manifest.json').read_bytes()
        return {'hash':digest(raw),'manifest':json.loads(raw)}
    @app.middleware('http')
    async def lost_ack(request,call_next):
        response=await call_next(request)
        marker=root/'lose-next-save-ack'
        if request.method=='POST' and request.url.path.startswith('/review-records/targets/') and response.status_code==200 and marker.exists():
            marker.unlink()
            with (root/'injected-failures.jsonl').open('a') as f:f.write('{"fault":"lost_save_ack_after_commit"}\n')
            return JSONResponse({'error':'Synthetic lost acknowledgment. Retry the same save.'},status_code=503)
        return response
    return app


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path);p.add_argument('--node',required=True,type=Path);a=p.parse_args()
    if not a.root.resolve().is_relative_to(ROOT/'outputs/prowl/testing'):raise ValueError('Dedicated testing root required')
    import uvicorn
    uvicorn.run(build(a.root.resolve(),a.node.resolve()),host='127.0.0.1',port=8020,access_log=False)
