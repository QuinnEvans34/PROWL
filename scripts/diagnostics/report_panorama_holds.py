"""Summarize retained audit evidence without rereading images or clearing holds."""
import argparse
from collections import Counter
import json
from pathlib import Path


def report(audit):
    rows = [json.loads(line) for line in (audit / 'cases.jsonl').read_text().splitlines()]
    summary = json.loads((audit / 'summary.json').read_text())
    resources = json.loads((audit / 'resources.json').read_text())
    assert summary['completed'] and resources['workers_reaped']
    assert len(rows) == len({r['study_id'] for r in rows}) == 2238
    assert dict(Counter(r['status'] for r in rows)) == summary['counts']
    holds = [r for r in rows if r['status'] == 'technical_hold']
    strata = Counter((r['disposition'], r['status']) for r in rows)
    return dict(training_ready=False, source_modified=False,
        strata=[dict(disposition=d, status=s, count=n) for (d,s),n in sorted(strata.items())],
        holds=[dict(study_id=r['study_id'], disposition=r['disposition'], reason=r['reason'],
                    ct_shape=r.get('ct_shape'), label_shape=r.get('label_shape'),
                    max_affine_difference=r.get('max_affine_difference')) for r in holds],
        next_actions={
            'grid': 'Review physical displacement; no tolerance relaxation or source-header edits.',
            'size': 'Retain 256M voxel cap; broader geometry needs separately tested bounded processing.',
            'duplicates': 'Requires calibrated exact/approximate comparison covering protected PanTS roles.',
            'protection': 'Current no-test-CT-read instruction prevents a complete fresh overlap scan; obtain explicit scope or verified fingerprints.',
            'non_pdac': 'Remain generic-lesion unknown, including three manual anomalies; technical pass does not clear quarantine.'})


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=report(args.audit)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['strata'],indent=2))
