#!/usr/bin/env python3
"""Loopback FastAPI review writer; no training or inference is started."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from jsonschema import ValidationError
from src.review.store import ReviewStore, ReviewError, FILES, digest


def create_app(store, *, port=8018, attachments=None):
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Invalid loopback review port')
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware('http')
    async def local(request, call_next):
        if (request.headers.get('host') not in (f'127.0.0.1:{port}',f'localhost:{port}','127.0.0.1:5180','localhost:5180')
                or request.headers.get('origin') not in (None,'http://127.0.0.1:5180','http://localhost:5180')
                or request.headers.get('sec-fetch-site') == 'cross-site'):
            return JSONResponse({'error':'Local access required.'}, status_code=403)
        try: response = await call_next(request)
        except ReviewError as error: response = JSONResponse({'error':str(error)}, status_code=error.status)
        except (ValueError, KeyError, TypeError, ValidationError): response = JSONResponse({'error':'Invalid review or package.'}, status_code=400)
        except OSError: response = JSONResponse({'error':'Review storage or prediction service is unavailable. Your draft has not been cleared.'}, status_code=503)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/review-records/packages')
    def packages(): return {'packages':store.packages()}

    @app.get('/review-records/packages/{identity}/files/{name}')
    def artifact(identity: str, name: str):
        if name not in {'manifest.json', *FILES.values()}: raise ReviewError('Unknown file.',404)
        raw, m, current = store.manifest('archive/'+identity)
        if name == 'manifest.json': data = raw
        else:
            ref = next(m['files'][k] for k, value in FILES.items() if value == name)
            data = store.reader('archive/'+identity)(name, ref['bytes'])
            if len(data) != ref['bytes'] or digest(data) != ref['content_sha256']: raise ReviewError('Retained prediction changed.')
        return Response(data, media_type='application/gzip' if name.endswith('.gz') else 'application/json')

    @app.get('/review-records/targets/{source:path}')
    def target(source: str): return store.target(source)

    @app.post('/review-records/targets/{source:path}')
    async def save(source: str, request: Request):
        if request.headers.get('content-type') != 'application/json' or request.headers.get('transfer-encoding'):
            raise ReviewError('JSON request required.',400)
        size = int(request.headers.get('content-length','0'))
        if not 0 < size <= 8192: raise ReviewError('Review request exceeds its limit.',400)
        raw = await request.body()
        if len(raw) != size: raise ReviewError('Invalid request size.',400)
        # File I/O runs in a worker thread rather than blocking the ASGI event loop.
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(store.append, source, json.loads(raw))

    if attachments is not None:
        from src.review.literature_attachment_api import register_attachment_routes
        register_attachment_routes(app, attachments)
    return app


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True, type=Path)
    p.add_argument('--saved-package', type=Path)
    p.add_argument('--port', type=int, default=8018, help='Loopback port; use a separate port and root for isolated verification')
    p.add_argument('--attachments', type=Path, help='Existing dedicated literature attachment root')
    p.add_argument('--node', type=Path, help='Node24 runtime required with --attachments')
    args = p.parse_args()
    if args.attachments and not args.node: p.error('--node required with --attachments')
    import uvicorn
    store = ReviewStore(args.root, args.saved_package, floor_bytes=50_000_000_000)
    attachments = None
    if args.attachments:
        from src.review.literature_attachments_v1 import LiteratureAttachments
        attachments = LiteratureAttachments(args.attachments, store, node=args.node)
    uvicorn.run(create_app(store, port=args.port, attachments=attachments), host='127.0.0.1', port=args.port, access_log=False)
