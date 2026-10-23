"""CPU-only inspection of saved failed qualification; no model execution or retry."""
import json
import os
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    import torch
    from scripts.diagnostics import setup_fast_varied as setup
    from src.training.experiment_config import sha256
    if torch.cuda.is_available():
        raise ValueError('CPU-isolated saved-evidence inspection required')
    torch.set_num_threads(2)
    setup.check_pins()
    for path, pin in setup.read(setup.SETUP/'cuda-request.json')['pins'].items():
        if sha256(path) != pin:
            raise ValueError('Qualification producer changed')
    resource = setup.read(setup.SETUP/'cuda-producer-resources.json')
    if resource['success'] or resource['exit_code'] != 1 or not resource['workers_reaped']:
        raise ValueError('Expected failed, reaped stage')
    output = setup.SETUP/'cuda'
    paths = [output/'reference-final.pt', output/'expected.pt',
             output/'reference.json', output/'execution/history.jsonl']
    a = torch.load(paths[0], map_location='cpu', weights_only=True)
    b = torch.load(paths[1], map_location='cpu', weights_only=True)
    reference = setup.read(paths[2])['updates']
    journal = [json.loads(line) for line in paths[3].read_text().splitlines()]
    candidate = [row for row in journal if row['event'] == 'update']
    if len(reference) != 33 or len(candidate) != 33:
        raise ValueError('Incomplete saved update evidence')
    exact_inputs = all(all(x[k] == y[k] for k in
        ('step', 'member_id', 'batch_sha256', 'input_view', 'learning_rate'))
        for x, y in zip(reference, candidate))
    rows = []
    def tensors(x, y, path):
        if isinstance(x, torch.Tensor):
            if x.dtype != y.dtype or x.shape != y.shape:
                raise ValueError('Shape/type changed')
            if x.is_floating_point():
                difference = (x-y).abs()
                bad = ~torch.isclose(x, y, rtol=1.3e-6, atol=1e-5)
                rows.append(dict(path=path, elements=x.numel(), mismatches=int(bad.sum()),
                    max_absolute_difference=float(difference.max()),
                    difference_l2=float(torch.linalg.vector_norm((x-y).double())),
                    reference_l2=float(torch.linalg.vector_norm(x.double()))))
            elif not torch.equal(x, y):
                raise ValueError('Integer state differs: '+path)
        elif isinstance(x, dict):
            if x.keys() != y.keys(): raise ValueError('State keys changed')
            for key in x: tensors(x[key], y[key], path+'/'+str(key))
        elif isinstance(x, (list, tuple)):
            if len(x) != len(y): raise ValueError('State length changed')
            for i, (left, right) in enumerate(zip(x, y)): tensors(left, right, path+'/'+str(i))
        elif x != y:
            raise ValueError('Scalar state differs: '+path)
    for key in ('model', 'optimizer', 'step', 'exposure', 'cpu_rng', 'cuda_rng', 'mps_rng'):
        tensors(a['raw'][key], b['raw'][key], key)
    tensors(a['focused'], b['focused'], 'focused')
    indices = [i for i in range(6, 33) if i % 5 != 0]
    old = statistics.mean(reference[i]['update_seconds'] for i in indices)
    new = statistics.mean(candidate[i]['update_seconds'] for i in indices)
    loss_differences = [abs(x['loss']-y['loss']) for x, y in zip(reference, candidate)]
    result = dict(status='BLOCKED_NUMERICAL_EQUIVALENCE', qualified=False,
        source_sha256={str(p):sha256(p) for p in paths}, exact_inputs=exact_inputs,
        updates_each=33, optimizer_updates_in_this_review=0, CT_reads=0, test_reads=0,
        scalar_integer_rng_exposure_focus_state_exact=True,
        first_loss_difference_step=next((i+1 for i, v in enumerate(loss_differences) if v), None),
        maximum_loss_difference=max(loss_differences),
        floating_elements=sum(r['elements'] for r in rows),
        mismatched_elements=sum(r['mismatches'] for r in rows),
        maximum_state_absolute_difference=max(r['max_absolute_difference'] for r in rows),
        failing_tensors=[r for r in rows if r['mismatches']],
        reference_mean_update_seconds=old, candidate_mean_update_seconds=new,
        observed_update_speedup=old/new,
        speedup_status='Descriptive only; does not override failed equivalence gate',
        native_cases=sum(r['event']=='native_case' for r in journal),
        worker_reaped=True, cold_stage_started=False, scientific_launch_started=False,
        causal_conclusion='Unresolved; input equality alone does not prove numerical equivalence')
    setup.write(setup.SETUP/'failure-review.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise ValueError('Explicit CPU isolation required')
    main()
