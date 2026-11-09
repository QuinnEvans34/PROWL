#!/usr/bin/env python3
"""Opt-in single-call candidate. Requires exclusive accelerator admission; no auto-promotion."""
import argparse
from contextlib import nullcontext
from pathlib import Path
from serve_literature_search import create_service, create_study_answers, handler_for, LocalFixtureServer
from src.retrieval.single_pass_summary import SinglePassAnswers
from src.operations.full_training_platform import training_guard
ROOT=Path(__file__).resolve().parents[1]
def run_candidate(config, port, *, sources_only=False):
    with (nullcontext() if sources_only else training_guard(ROOT/'outputs/prowl/.mps-profile.lock')):
        service=create_service(config); sources,_=create_study_answers(service)
        service.answer_gpu_reserved = not sources_only
        class SourceOnlyAnswers:
            policy = 'sources-only'
        handler = handler_for(service,sources,SourceOnlyAnswers() if sources_only else SinglePassAnswers(sources))
        class SourceOnlyHandler(handler):
            def do_POST(self):
                if self.path in ('/literature-search/answer','/literature-search/interpret'):
                    if not self.local(): return self.reply(403, {'error':'Local access required.'})
                    return self.reply(409, {'error':'Source search is ready. Live AI answers require AC power and a free local GPU; use Find sources.'})
                return super().do_POST()
        try:
            server=LocalFixtureServer(('127.0.0.1',port),SourceOnlyHandler if sources_only else handler)
            try: server.serve_forever()
            finally: server.server_close()
        finally:
            service.answer_gpu_reserved = False

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--port',type=int,default=8021)
    p.add_argument('--sources-only',action='store_true',help='CPU source search only; rejects answer/model-help requests')
    a=p.parse_args()
    run_candidate(a.config,a.port,sources_only=a.sources_only)
