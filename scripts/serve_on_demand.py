#!/usr/bin/env python3
"""Loopback prediction job API. Starts unconfigured unless an operator supplies pins."""
import argparse
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.inference.on_demand import PredictionJobs, JobError, canonical
from scripts.serve_evidence_fixture import LocalFixtureServer

PREFIX = '/scan-inference'


def handler_for(jobs):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def reply(self, status, value):
            self.send_bytes(status, canonical(value), 'application/json')

        def send_bytes(self, status, data, mime):
            self.send_response(status)
            for key, value in [('Content-Type', mime), ('Content-Length', str(len(data))),
                               ('Cache-Control','no-store'), ('X-Content-Type-Options','nosniff')]:
                self.send_header(key, value)
            self.end_headers()
            try: self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError): pass

        def local(self):
            hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}',
                     '127.0.0.1:5180', 'localhost:5180'}
            return (self.headers.get('Host') in hosts
                    and self.headers.get('Origin') in (None, 'http://127.0.0.1:5180', 'http://localhost:5180')
                    and self.headers.get('Sec-Fetch-Site') != 'cross-site')

        def route(self):
            if not self.local(): return self.reply(403, {'error':'Local access required.'})
            try:
                if self.command == 'GET' and self.path == PREFIX+'/cases':
                    return self.reply(200, jobs.catalog())
                if self.command == 'POST' and self.path == PREFIX+'/jobs':
                    n = int(self.headers.get('Content-Length', '0'))
                    if not 0 < n <= 512 or self.headers.get('Content-Type') != 'application/json' or self.headers.get('Transfer-Encoding'):
                        raise ValueError()
                    body = json.loads(self.rfile.read(n))
                    if not isinstance(body, dict) or set(body) != {'case_id'} or not isinstance(body['case_id'], str):
                        raise ValueError()
                    return self.reply(202, jobs.submit(body['case_id']))
                match = re.fullmatch(PREFIX+r'/jobs/([a-f0-9]{32})(?:/(cancel|files/(manifest.json|ct.nii.gz|prediction.nii.gz|result.json|evidence.json)))?', self.path)
                if not match: return self.reply(404, {'error':'Unknown route.'})
                job_id, suffix, filename = match.groups()
                if self.command == 'POST' and suffix == 'cancel':
                    return self.reply(200, jobs.cancel(job_id))
                if self.command == 'DELETE' and suffix is None:
                    jobs.release(job_id)
                    return self.reply(200, {'released': True})
                if self.command == 'GET' and suffix is None:
                    return self.reply(200, jobs.get(job_id))
                if self.command == 'GET' and filename:
                    p = jobs.artifact(job_id, filename)
                    return self.send_bytes(200, p.read_bytes(), 'application/gzip' if filename.endswith('.gz') else 'application/json')
                self.reply(404, {'error':'Unknown route.'})
            except JobError as error:
                self.reply(error.status, {'error': error.message})
            except (ValueError, KeyError, TypeError, UnicodeError):
                self.reply(400, {'error':'Invalid inference request.'})
            except OSError:
                self.reply(503, {'error':'Inference storage is unavailable.'})

        do_GET = route
        do_POST = route
        do_DELETE = route
    return Handler


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path)
    p.add_argument('--port', type=int, default=8017)
    args = p.parse_args()
    # Session-owned temporary transport; optional persistent caching is intentionally not enabled.
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix='prowl-inference-') as directory:
        jobs = PredictionJobs(directory, json.loads(args.config.read_text()) if args.config else None)
        server = LocalFixtureServer(('127.0.0.1', args.port), handler_for(jobs))
        print(f'Prediction API on 127.0.0.1:{args.port}; configured={args.config is not None}', flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally:
            jobs.close()
            server.server_close()
