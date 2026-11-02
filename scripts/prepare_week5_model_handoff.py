"""Export a hash-bound, independently backed-up selected control on CPU only.

No inference, optimizer construction, cohort selection, or network transfer.
Private artifact destinations must be outside the checkout.
"""
import argparse
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
from src.inference.cascade_models_v1 import architecture, load_weights


def bound(path, expected, limit=256 * 1024**2):
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > limit:
        raise ValueError('Regular bounded input required')
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Input SHA256 mismatch')
    return raw


def export_control(request, destination):
    if request['step'] != 20000:
        raise ValueError('This packet binds the preselected 20000 control only')
    out = Path(destination).resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValueError('Private destination must be outside checkout')
    if out.exists():
        raise FileExistsError('Fresh destination required')
    payload = bound(request['checkpoint'], request['checkpoint_sha256'])
    if bound(request['backup'], request['checkpoint_sha256']) != payload:
        raise ValueError('Independent checkpoint mismatch')
    if Path(request['checkpoint']).stat().st_dev == Path(request['backup']).stat().st_dev:
        raise ValueError('Independent backup filesystem required')
    report_bytes = bound(request['selection_report'], request['selection_report_sha256'], 16 * 1024**2)
    if bound(request['selection_backup'], request['selection_report_sha256'], 16 * 1024**2) != report_bytes:
        raise ValueError('Independent selection mismatch')
    report = json.loads(report_bytes)
    saved = torch.load(io.BytesIO(payload), weights_only=True, map_location='cpu')
    session = saved['session']; raw = session['student']['raw']
    if raw['step'] != request['step'] or report['step'] != raw['step'] or report.get('endpoint') != 'selected':
        raise ValueError('Selected checkpoint step mismatch')
    if report['scope'] != 'native_provided_pancreas_region_development':
        raise ValueError('Unexpected evaluation scope')
    if session['identity']['loss']['max_weight'] != 0.0:
        raise ValueError('Only completed zero-KD control is eligible for this export')
    if raw['identity']['architecture'] != architecture('segmenter'):
        raise ValueError('Architecture mismatch')
    control = raw['identity']['control']
    if (set(control['train']) & set(control['validation']) or
            len(set(control['train'])) != len(control['train']) or
            len(set(control['validation'])) != len(control['validation'])):
        raise ValueError('Invalid cohort roles')
    if set(r['case_id'] for r in report['cases']) != set(control['validation']) or len(report['cases']) != len(control['validation']):
        raise ValueError('Selection report cohort mismatch')
    state = raw['model']
    if not state or any(type(v) is not torch.Tensor or v.dtype != torch.float32 or
                        not torch.isfinite(v).all().item() for v in state.values()):
        raise ValueError('Finite float32 weights required')
    bundle = dict(format='prowl-cascade-weights-1', role='segmenter',
                  architecture=architecture('segmenter'),
                  source_checkpoint_sha256=request['checkpoint_sha256'], state_dict=deepcopy(state))
    out.mkdir(parents=True)
    target = out / 'segmenter-control-020000.pt'
    with target.open('xb') as f:
        torch.save(bundle, f)
    pin = hashlib.sha256(target.read_bytes()).hexdigest()
    model, receipt = load_weights(target, expected_sha256=pin, role='segmenter')
    if any(not torch.equal(model.state_dict()[k], v) for k, v in state.items()):
        raise ValueError('Exported tensors differ')
    provenance = dict(version='week5-control-export-1', step=raw['step'],
                      checkpoint_sha256=request['checkpoint_sha256'],
                      selection_report_sha256=request['selection_report_sha256'],
                      selected_development_dice=report['lesion_positive_macro_dice'],
                      weights=receipt, raw_identity=raw['identity'],
                      distillation_identity=session['identity'], independent_backup_verified=True,
                      exported_tensors_exact=True, gpu_used=False, inference_performed=False,
                      limitations=['Development-selected checkpoint; not independent acceptance.',
                                   'Physical-window inference required; old resized-crop cascade is not qualified.',
                                   'Pretrained membership and biological patient independence unresolved.'])
    (out / 'control-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return provenance


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = export_control(json.loads(bound(args.request, args.request_sha256, 1024**2)), args.output)
    print(json.dumps(dict(step=result['step'], weights=result['weights'], gpu_used=False)))
