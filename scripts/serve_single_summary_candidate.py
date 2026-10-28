#!/usr/bin/env python3
"""Opt-in single-call candidate. Requires exclusive accelerator admission; no auto-promotion."""
import argparse
from pathlib import Path
from serve_literature_search import create_service, create_study_answers, handler_for, LocalFixtureServer
from src.retrieval.single_pass_summary import SinglePassAnswers
from src.operations.full_training_platform import training_guard
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--port',type=int,default=8021)
    a=p.parse_args()
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        service=create_service(a.config); sources,_=create_study_answers(service)
        server=LocalFixtureServer(('127.0.0.1',a.port),handler_for(service,sources,SinglePassAnswers(sources)))
        try: server.serve_forever()
        finally: server.server_close()
