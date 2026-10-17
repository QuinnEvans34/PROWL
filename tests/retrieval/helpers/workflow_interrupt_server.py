"""Owned HTTP process for the restart regression; synthetic callbacks, no DB/model calls."""
import argparse
import json
import os
from pathlib import Path
import sys
from threading import Event

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from serve_research_workflow import LocalFixtureServer, workflow_handler
from src.retrieval import grounded_answer
from src.retrieval.research_workflow import ResearchWorkflow, publish


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mode', choices=('interrupt', 'recover'), required=True)
    args = parser.parse_args()
    payload = json.loads((args.root / 'inputs.json').read_text())

    def call(kind, value=None):
        with (args.root / 'calls.jsonl').open('a') as log:
            log.write(json.dumps(dict(kind=kind, mode=args.mode)) + '\n')
            log.flush()
            os.fsync(log.fileno())
        if args.mode == 'recover' or kind == 'model_api':
            raise AssertionError('Recovery must reuse verified work; model API is forbidden')
        return value

    grounded_answer.api = lambda *_args, **_kw: call('model_api')

    class PausedWorkflow(ResearchWorkflow):
        def _validate(self, stage, *values):
            super()._validate(stage, *values)
            if args.mode == 'interrupt' and stage == 'validate':
                # select.json AND its completed event have been published. Stop before
                # validate.json/any response exists. The parent kills this owned process.
                publish(args.root / 'barrier.json', dict(pid=os.getpid(), stage=stage))
                if not Event().wait(20):
                    raise TimeoutError('Test controller did not terminate the paused worker')

    store = PausedWorkflow(args.root / 'runs', lambda _: call('retrieve', payload['passages']),
        'research-v1', 'fixture-encoder', 'fixture-corpus',
        lambda *_: call('select', payload['generation']), dict(model='fixture'))
    server = LocalFixtureServer(('127.0.0.1', 0), workflow_handler(store))
    publish(args.root / f'{args.mode}-ready.json', dict(pid=os.getpid(), port=server.server_port))
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
