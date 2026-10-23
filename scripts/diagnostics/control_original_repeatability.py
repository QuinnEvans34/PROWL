"""One approved 33-update original-loader repeatability control; no promotion."""
import argparse
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.diagnostics import qualify_fast_varied as qualification
from scripts.diagnostics import setup_fast_varied as setup
from src.operations.full_training_platform import training_guard, watch_windows, require_ac
from src.training.experiment_config import sha256

OUT = setup.SETUP/'original-repeatability-a01'
SECONDS = 600
RSS_BYTES = 12*1024**3
UPDATES = 33


def compare_states(a, b):
    """Describe differences under the ORIGINAL bound; never waive that bound."""
    import torch
    floating = []
    exact_other = True
    def visit(left, right, path):
        nonlocal exact_other
        if isinstance(left, torch.Tensor):
            if not isinstance(right, torch.Tensor) or left.dtype != right.dtype or left.shape != right.shape:
                raise ValueError('State tensor signature changed: '+path)
            if left.is_floating_point():
                if not torch.isfinite(left).all() or not torch.isfinite(right).all():
                    raise ValueError('Nonfinite saved state')
                delta = (left-right).double()
                floating.append(dict(path=path, elements=left.numel(),
                    mismatches=int((~torch.isclose(left, right, rtol=1.3e-6, atol=1e-5)).sum()),
                    max_absolute_difference=float(delta.abs().max()),
                    difference_l2=float(torch.linalg.vector_norm(delta)),
                    reference_l2=float(torch.linalg.vector_norm(left.double()))))
            else:
                exact_other = exact_other and torch.equal(left, right)
        elif isinstance(left, dict):
            if not isinstance(right, dict) or left.keys() != right.keys():
                raise ValueError('State keys changed: '+path)
            for key in left: visit(left[key], right[key], path+'/'+str(key))
        elif isinstance(left, (list, tuple)):
            if type(left) is not type(right) or len(left) != len(right):
                raise ValueError('State sequence changed: '+path)
            for i, (x, y) in enumerate(zip(left, right)): visit(x, y, path+'/'+str(i))
        else:
            exact_other = exact_other and left == right
    for key in ('model', 'optimizer', 'step', 'exposure', 'cpu_rng', 'cuda_rng', 'mps_rng'):
        visit(a['raw'][key], b['raw'][key], key)
    visit(a['focused'], b['focused'], 'focused')
    groups = {}
    for group in ('model', 'optimizer'):
        rows = [r for r in floating if r['path'].startswith(group+'/')]
        groups[group] = dict(elements=sum(r['elements'] for r in rows),
            mismatches=sum(r['mismatches'] for r in rows),
            max_absolute_difference=max((r['max_absolute_difference'] for r in rows), default=0),
            difference_l2=math.sqrt(sum(r['difference_l2']**2 for r in rows)),
            reference_l2=math.sqrt(sum(r['reference_l2']**2 for r in rows)))
    return dict(rtol=1.3e-6, atol=1e-5, scalar_integer_rng_counters_exact=bool(exact_other),
        floating_elements=sum(r['elements'] for r in floating),
        mismatched_elements=sum(r['mismatches'] for r in floating),
        max_absolute_difference=max((r['max_absolute_difference'] for r in floating), default=0),
        passes_original_bound=bool(exact_other and not any(r['mismatches'] for r in floating)),
        groups=groups, failing_tensors=[r for r in floating if r['mismatches']])


def input_comparison(a, b):
    fields = ('step', 'member_id', 'batch_sha256', 'input_view', 'learning_rate')
    if len(a) != UPDATES or len(b) != UPDATES or any(
        any(x[k] != y[k] for k in fields) for x, y in zip(a, b)):
        raise ValueError('Original-control actual input sequence mismatch')
    differences = [abs(x['loss']-y['loss']) for x, y in zip(a, b)]
    return dict(exact_inputs=True, first_loss_difference_step=next(
        (i+1 for i, d in enumerate(differences) if d), None), max_loss_difference=max(differences))


def check_prior():
    qualification.check()
    reference = setup.read(setup.SETUP/'cuda-reference-resources.json')
    failed = setup.read(setup.SETUP/'cuda-producer-resources.json')
    if not reference['success'] or reference['exit_code'] != 0 or not reference['workers_reaped']:
        raise ValueError('Reference not complete/reaped')
    if failed['success'] or failed['exit_code'] != 1 or not failed['workers_reaped']:
        raise ValueError('Expected preserved failed/reaped qualification')
    plan = setup.read(setup.SETUP/'cuda-plan.json')
    if plan['updates'] != UPDATES or len(plan['train']) != 12 or not plan['nonpromotable']:
        raise ValueError('Approved control scope differs')


def run_original(output):
    # Only the destination changes. Reuse the frozen function, loader and session.
    original_output = qualification.OUT
    try:
        qualification.OUT = output
        qualification.original_worker()
    finally:
        qualification.OUT = original_output


def worker():
    import torch
    check_prior()
    for path, pin in setup.read(OUT/'request.json')['pins'].items():
        if sha256(path) != pin: raise ValueError('Control input/producer changed: '+path)
    setup.write(OUT/'backend-settings.json', dict(torch_version=torch.__version__,
        cuda_version=torch.version.cuda, cudnn_benchmark=torch.backends.cudnn.benchmark,
        cudnn_deterministic=torch.backends.cudnn.deterministic,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        cublas_workspace_config=os.environ.get('CUBLAS_WORKSPACE_CONFIG'),
        note='Observed before unchanged Session.rng_scope, which disables TF32 during updates'))
    run_original(OUT)
    original = setup.read(setup.SETUP/'cuda/reference.json')['updates']
    control = setup.read(OUT/'reference.json')['updates']
    inputs = input_comparison(original, control)
    paths = [setup.SETUP/'cuda/reference-final.pt', OUT/'reference-final.pt', setup.SETUP/'cuda/expected.pt']
    a, b, fast = [torch.load(p, map_location='cpu', weights_only=True) for p in paths]
    if a['identity'] != b['identity'] or a['identity_sha256'] != b['identity_sha256']:
        raise ValueError('Original control model identity changed')
    repeated = compare_states(a, b)
    existing_fast = compare_states(a, fast)
    other_fast = compare_states(b, fast)
    result = dict(completed=True, diagnostic_only=True, scientific_updates=0,
        engineering_updates=UPDATES, native_evaluations=0, test_reads=0,
        source_audit_replayed=False, **inputs, identity_exact=True,
        original_repeat=repeated, original_vs_fast=existing_fast, repeat_vs_fast=other_fast,
        prior_qualification_status='FAILED_PRESERVED', ready_for_scientific_launch=False,
        source_sha256={str(p):sha256(p) for p in paths},
        interpretation=('Original loader also exceeds the original numerical bound across independent runs; '
            'this demonstrates baseline non-repeatability, not proof of optimized-loader equivalence.'
            if not repeated['passes_original_bound'] else
            'Original repetition passes the bound; the optimized-path discrepancy remains unresolved.'),
        limitations='One additional original run, not a distribution or a revised acceptance threshold')
    setup.write(OUT/'result.json', result)
    print(result['interpretation'], flush=True)


def admission():
    if OUT.exists(): raise ValueError('Control already started; no duplicate/retry')
    check_prior()


def launch():
    admission()
    paths = [Path(__file__), ROOT/'tests/test_original_repeatability.py',
        setup.SETUP/'cuda-plan.json', setup.SETUP/'cuda-request.json',
        setup.SETUP/'cuda/reference.json', setup.SETUP/'cuda/reference-final.pt',
        setup.SETUP/'cuda/expected.pt', setup.SETUP/'failure-review.json',
        setup.SETUP/'original-repeatability-tests.xml']
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        OUT.mkdir(exist_ok=False)
        setup.write(OUT/'request.json', dict(seconds=SECONDS, rss_bytes=RSS_BYTES,
            updates=UPDATES, authority='User: Yes, run it. Single original-loader repeatability control.',
            pins={str(p):sha256(p) for p in paths}, scientific=False, retry=False))
        env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PROWL_ORIGINAL_CONTROL='1')
        env.pop('CUDA_VISIBLE_DEVICES', None)
        with (OUT/'worker.log').open('x') as stream:
            process = subprocess.Popen([sys.executable, __file__, '--worker'], cwd=ROOT,
                stdout=stream, stderr=subprocess.STDOUT, env=env)
            success = False
            try:
                watch_windows(process, seconds=SECONDS, rss_bytes=RSS_BYTES, tick=require_ac)
                success = True
            finally:
                setup.write(OUT/'resources.json', dict(getattr(process, 'duration_resources', {}),
                    success=success, exit_code=process.returncode))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run', action='store_true')
    group.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.run: launch()
    else:
        if os.environ.get('PROWL_ORIGINAL_CONTROL') != '1': raise ValueError('Supervisor required')
        worker()
