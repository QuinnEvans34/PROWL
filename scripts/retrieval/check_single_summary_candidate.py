#!/usr/bin/env python3
"""Five exposed packets. Preparation is CPU-only; live evaluation needs a free GPU."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.operations.full_training_platform import training_guard
from src.retrieval.single_pass_summary import generate, POLICY, FINGERPRINT, MODEL, MODEL_SHA
from src.retrieval.natural_answer import api

NAMES = ('function', 'function_paraphrase', 'methods', 'fat', 'gap')


def prepare(output, source=None):
    source = source or ROOT/'outputs/prowl/general-fallback-20261023'
    packets = []
    # Check every input before creating output or making any model call.
    for name in NAMES:
        raw = (source/f'{name}.json').read_bytes()
        packet = json.loads(raw)
        question, evidence = packet['question'], packet['baseline']['evidence']
        if not isinstance(question, str) or not question.strip():
            raise ValueError('Missing question')
        if not 1 <= len(evidence) <= 5 or sum(len(e['record']['text']) for e in evidence) > 16000:
            raise ValueError('Evidence budget')
        ranks = [e['rank'] for e in evidence]
        if len(set(ranks)) != len(ranks):
            raise ValueError('Duplicate evidence rank')
        packets.append(dict(name=name, question=question, evidence=evidence,
                            source_sha256=hashlib.sha256(raw).hexdigest()))
    output.mkdir(exist_ok=False)
    manifest = dict(policy=POLICY, prompt_sha256=FINGERPRINT, model=MODEL,
                    model_sha256=MODEL_SHA, exposed_development=True, promoted=False,
                    packets=packets)
    (output/'inputs.json').write_text(json.dumps(manifest, indent=2))
    write_review(output, manifest, {})
    return manifest


def write_review(output, manifest, results):
    lines = ['# Single-call summary review', '',
             'Exposed development questions; not independent evaluation. No automatic promotion.', '',
             'Review factual support, completeness, qualifications, readability, citations and refusal behavior separately. '
             'Recorded time covers the saved-evidence generation path, not live retrieval or UI latency.', '']
    for packet in manifest['packets']:
        name = packet['name']
        lines += [f"## {name}: {packet['question']}", '']
        result = results.get(name)
        if result is None:
            lines += ['Not run. No model answer is available.', '']
        elif 'failure' in result:
            lines += [f"**Failed:** {result['failure']}", f"Elapsed: {result['seconds']:.2f}s", '']
        else:
            answer = result['answer']
            lines += [f"Coverage: {answer['coverage']}; elapsed: {result['seconds']:.2f}s", '']
            for claim in answer['claims']:
                lines += [claim['text'], '']
                for citation in claim['citations']:
                    lines += [f"Source [{citation['rank']}] supporting quotation:", '', citation['quote'], '']
            if answer['limitation']:
                lines += ['Limitation: '+answer['limitation'], '']
        lines += ['Manual review: **Pending**', '', '### Retrieved evidence', '']
        for evidence in packet['evidence']:
            record = evidence['record']
            lines += [f"**[{evidence['rank']}] {record['citation']['title']}**", '', record['text'], '']
        lines += [f"Input file SHA256: `{packet['source_sha256']}`", '']
    (output/'review.md').write_text('\n'.join(lines))


def evaluate(output, manifest, transport=api):
    results = {}
    for packet in manifest['packets']:
        started = time.monotonic()
        trace = []
        def call(path, payload=None):
            response = transport(path, payload, deadline=started+60)
            if path == 'chat':
                trace.append(dict(request=payload, response=response))
            return response
        result = dict(question=packet['question'], manual_review_required=True, promoted=False)
        try:
            result['answer'] = generate(packet['question'], packet['evidence'], call)
        except Exception as error:
            result['failure'] = repr(error)
        result.update(seconds=time.monotonic()-started, calls=trace)
        (output/f"{packet['name']}.json").write_text(json.dumps(result, indent=2))
        results[packet['name']] = result
        write_review(output, manifest, results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true', help='Snapshot inputs and readable passages without any model or GPU call')
    args = parser.parse_args()
    if args.prepare_only:
        prepare(args.output)
    else:
        with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
            evaluate(args.output, prepare(args.output))
