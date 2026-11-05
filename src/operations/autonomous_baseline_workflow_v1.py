"""Registered saved-baseline admission → error analysis → reviewer handoff.

Consumes the completed autonomous70 metadata export, never CT arrays or models.
The inference/scoring attempt remains external and unchanged; this integrates its
retained result into the existing recoverable CPU workflow, not a new GPU runner.
"""
import hashlib
from pathlib import Path

from src.operations.autonomous_baseline_review_v1 import read_bound, review
from src.operations.workflow_plan_v1 import Stage, encoded, sha


def definition(source, export_sha256, request_sha256, ready_sha256):
    source = Path(source).resolve()
    repo = Path(__file__).resolve().parents[2]
    producing = [Path(__file__), repo/'src/operations/autonomous_baseline_review_v1.py',
                 repo/'src/operations/workflow_plan_v1.py', repo/'src/operations/workflow_execution_v1.py',
                 repo/'src/operations/workflow_contracts_v1.py', repo/'src/operations/artifact_store.py']
    producer = sha({str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in producing})

    def checked():
        document = read_bound(source, export_sha256)
        result = review(document, request_sha256=request_sha256, ready_sha256=ready_sha256)
        return document, result

    def admission():
        document, result = checked()
        return dict(schema='autonomous-baseline-admission-v1', export_sha256=export_sha256,
                    identities=result['identities'], scope=result['scope'],
                    dispositions=[{k:r[k] for k in ('case_id','disposition','source_report_sha256')}
                                  for r in document['ordered_cases']],
                    local_verification=result['local_verification'])

    def analysis():
        return checked()[1]

    def handoff():
        result = analysis()
        return dict(schema='autonomous-baseline-review-handoff-v1', export_sha256=export_sha256,
                    identities=result['identities'], scope=result['scope'], aggregate=result['aggregate'],
                    failed_cases=result['failures'], review_queues=result['review_queues'],
                    limitations=result['limitations'],
                    reviewed_cases=[], review_decision=None, independent_acceptance=False,
                    image_payloads_attached=False, inference_recovery_qualified=False)

    builders = {'admission': ('admission.json', admission), 'analysis': ('analysis.json', analysis),
                'handoff': ('handoff.json', handoff)}
    validators = {}
    for sid, (name, build) in builders.items():
        def validate(files, name=name, build=build):
            if files != {name: encoded(build())}:
                raise ValueError('Saved baseline artifact differs from current verified source')
            return dict(export_sha256=export_sha256, scope='saved_exposed_development_metadata_only')
        validators[sid] = validate

    def produce(sid, parents):
        for dependency, files in parents.items():
            validators[dependency](files)
        name, build = builders[sid]
        return {name: encoded(build())}

    stages = [Stage('admission', inputs=dict(export=export_sha256, request=request_sha256, ready=ready_sha256), producer=producer),
              Stage('analysis', ('admission',), producer=producer),
              Stage('handoff', ('analysis',), producer=producer)]
    handlers = {sid: (lambda parents, config, sid=sid: produce(sid, parents)) for sid in builders}
    return stages, handlers, validators
