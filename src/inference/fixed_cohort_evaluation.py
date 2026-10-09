"""Fixed-cohort orchestration around existing CT-only prediction and offline scoring.

Prediction workers receive only an allowlisted CT request. References are opened
only by the separate score stage. This is not a new cohort admission authority.
"""
from collections import Counter
from contextlib import nullcontext
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = {'models', 'localizer_recipe', 'patch_size', 'tensor_shape', 'device',
            'max_sampling_voxels', 'region_policy'}
DEFAULTS = dict(max_sampling_voxels=16_000_000, region_policy='all_support')


def file_hash(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_pinned(path, pin):
    raw = Path(path).read_bytes()
    if sha256(raw).hexdigest() != pin:
        raise ValueError('Control checksum differs')
    return json.loads(raw)


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def require(value, message):
    if not value:
        raise ValueError(message)


def validate_plan(plan):
    require(set(plan) == {'version', 'cohort_id', 'inference', 'limits', 'cases', 'limitations'},
            'Exact evaluation plan fields required')
    require(plan['version'] == 1 and isinstance(plan['cohort_id'], str) and plan['cohort_id'],
            'Version and fixed cohort identity required')
    require(isinstance(plan['limitations'], list) and all(isinstance(x, str) for x in plan['limitations']),
            'Explicit limitations required')
    settings = plan['inference']
    require(SETTINGS - DEFAULTS.keys() <= settings.keys() <= SETTINGS, 'Unknown/missing inference settings')
    require(set(settings['models']) == {'localizer', 'segmenter'}, 'Two model roles required')
    for item in settings['models'].values():
        validate_file(item)
    require(settings.get('region_policy', 'all_support') in ('all_support', 'largest_component_26'),
            'Unknown region policy')
    require(settings['device'] in ('cpu', 'mps', 'cuda'), 'Explicit device required')
    for key in ('patch_size', 'tensor_shape'):
        require(len(settings[key]) == 3 and all(type(x) is int and 16 <= x <= 192 and x % 8 == 0
                                               for x in settings[key]), 'Invalid tensor/patch shape')
    require(type(settings.get('max_sampling_voxels', 16_000_000)) is int and
            0 < settings.get('max_sampling_voxels', 16_000_000) <= 64_000_000, 'Sampling allocation bound')
    limits = plan['limits']
    require(set(limits) == {'seconds_per_case', 'total_seconds', 'rss_bytes', 'free_floor_bytes'},
            'Explicit resource limits required')
    require(all(type(x) is int and x > 0 for x in limits.values()), 'Positive integer limits required')
    require(plan['cases'], 'Nonempty fixed case list required')
    ids = []
    for case in plan['cases']:
        require({'case_id', 'ct', 'references', 'reference_state', 'flags'} <= case.keys() <=
                {'case_id', 'ct', 'references', 'reference_state', 'flags', 'reuse', 'spatial_units_review'},
                'Unknown/missing case fields')
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', case['case_id']) is not None,
                'Safe case ID required')
        ids.append(case['case_id'])
        validate_file(case['ct'])
        require(case['reference_state'] in ('positive', 'reference_empty', 'unknown'), 'Reference state required')
        require(isinstance(case['flags'], list) and all(isinstance(x, str) for x in case['flags']), 'Case flags required')
        refs = case['references']
        require(set(refs) == {'pancreas', 'lesion', 'allow_unknown_units'}, 'Explicit scoring references required')
        require(type(refs['allow_unknown_units']) is bool, 'Explicit reference units policy required')
        for role in ('pancreas', 'lesion'):
            validate_file(refs[role])
        if 'reuse' in case:
            reuse = case['reuse']
            require(set(reuse) == {'directory', 'result_sha256', 'request'}, 'Pinned reuse request/receipt required')
            validate_file(reuse['request'])
            validate_file(dict(path=reuse['directory'], sha256=reuse['result_sha256']))
    require(len(ids) == len(set(ids)), 'Duplicate fixed case ID')
    return plan


def validate_file(item):
    require(set(item) == {'path', 'sha256'} and isinstance(item['path'], str) and
            Path(item['path']).is_absolute() and isinstance(item['sha256'], str) and
            re.fullmatch('[0-9a-f]{64}', item['sha256']) is not None, 'Absolute path and SHA256 required')


def prediction_request(plan, case, output):
    # Never copy case metadata or references into the worker request.
    request = dict(DEFAULTS, **plan['inference'], ct_path=case['ct']['path'],
                   ct_sha256=case['ct']['sha256'], case_id=case['case_id'], output_dir=str(output))
    if 'spatial_units_review' in case:
        request['spatial_units_review'] = case['spatial_units_review']
    return request


def request_identity(request):
    fields = SETTINGS | {'ct_path', 'ct_sha256', 'case_id', 'output_dir', 'spatial_units_review'}
    require(set(request) <= fields and SETTINGS - DEFAULTS.keys() <= request.keys(),
            'Not a CT-only request')
    value = dict(DEFAULTS, **request)
    # Drive roots and output location do not define content identity.
    for key in ('ct_path', 'output_dir'):
        value.pop(key, None)
    value['models'] = {role: item['sha256'] for role, item in value['models'].items()}
    return value


def verify_prediction(directory, request, result_pin=None):
    directory = Path(directory)
    result = (read_pinned(directory / 'result.json', result_pin) if result_pin else
              json.loads((directory / 'result.json').read_text()))
    require(result['status'] == 'complete' and result['case_id'] == request['case_id'] and
            result['reference_inputs_used'] is False, 'Incomplete or reference-assisted prediction')
    evidence = result['evidence']
    require(evidence['component'] == 'autonomous-cascade-v1' and evidence['reference_inputs_used'] is False,
            'Autonomous cascade evidence required')
    require(evidence['source_identity'] == dict(study_id=request['case_id'], ct_sha256=request['ct_sha256']),
            'Prediction CT identity differs')
    require(evidence['model_sha256'] == {k: v['sha256'] for k, v in request['models'].items()}, 'Model identity differs')
    for key in ('localizer_recipe', 'patch_size', 'device'):
        require(evidence[key] == request[key], f'Prediction {key} differs')
    require(evidence['localizer_decision'] == 'argmax_then_' + request.get('region_policy', 'all_support'),
            'Region policy differs')
    require(evidence['region_plan']['transform']['tensor_shape'] == request['tensor_shape'],
            'Prediction tensor shape differs')
    units = result['spatial_units']
    require(units['interpreted_units'] == 'mm' and units.get('review') == request.get('spatial_units_review'),
            'Prediction spatial unit review differs')
    require(file_hash(directory / 'prediction.nii.gz') == result['prediction_sha256'], 'Prediction checksum differs')
    return result


def run_predictions(plan, plan_pin, output, runner=None):
    validate_plan(plan)
    # Share the existing MPS lock with local training/diagnostics. Reuse needs no GPU.
    fresh_mps = plan['inference']['device'] == 'mps' and any('reuse' not in c for c in plan['cases'])
    context = (ROOT / 'outputs/prowl/.mps-profile.lock').open('a') if fresh_mps else nullcontext()
    with context as lock:
        if fresh_mps:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _run_predictions(plan, plan_pin, output, runner)


def _run_predictions(plan, plan_pin, output, runner=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'plan.json', plan)
    started = time.monotonic()
    limits = plan['limits']
    with (output / 'journal.jsonl').open('x') as journal:
        for case in plan['cases']:
            directory = output / case['case_id'] / 'prediction'
            request = prediction_request(plan, case, directory)
            row = dict(case_id=case['case_id'], plan_sha256=plan_pin,
                       request_identity=request_identity(request), status='failed')
            try:
                if 'reuse' in case:
                    reuse = case['reuse']; directory = Path(reuse['directory'])
                    prior = read_pinned(reuse['request']['path'], reuse['request']['sha256'])
                    require(Path(prior['output_dir']).resolve() == directory.resolve(), 'Saved request output location differs')
                    require(request_identity(prior) == request_identity(request), 'Incompatible saved prediction request')
                    verify_prediction(directory, request, reuse['result_sha256'])
                    row['status'] = 'reused'
                elif time.monotonic() - started >= limits['total_seconds'] or shutil.disk_usage(output).free < limits['free_floor_bytes']:
                    row['status'] = 'not_run_resource_limit'
                else:
                    directory.parent.mkdir()
                    request_path = directory.parent / 'request.json'
                    write_new(request_path, request)
                    remaining = min(limits['seconds_per_case'], limits['total_seconds'] - (time.monotonic() - started))
                    args = (request_path, directory.parent / 'inference.log', remaining, limits['rss_bytes'])
                    row['resources'] = (runner(*args) if runner else
                                        run_worker(*args, free_floor_bytes=limits['free_floor_bytes']))
                    verify_prediction(directory, request)
                    row['status'] = 'complete'
                row['directory'] = str(directory)
                if row['status'] in ('complete', 'reused'):
                    row['result_sha256'] = file_hash(directory / 'result.json')
            except Exception as exc:
                row.update(status='failed', error_type=type(exc).__name__, error=str(exc),
                           resources=getattr(exc, 'resources', row.get('resources')))
                receipt = directory / 'result.json'
                if receipt.exists():
                    try:
                        row['worker_result'] = json.loads(receipt.read_text())
                    except (ValueError, OSError) as receipt_error:
                        row['receipt_error'] = str(receipt_error)
            journal.write(json.dumps(row, allow_nan=False) + '\n'); journal.flush()
    return output / 'journal.jsonl'


def run_worker(request_path, log_path, seconds, rss_bytes, *, free_floor_bytes):
    # Reuse the existing owned-process watchdog, only when a new worker is needed.
    from src.operations.segmenter_duration_dispatch_v1 import watch
    with Path(log_path).open('x') as log:
        process = subprocess.Popen([sys.executable, str(ROOT / 'scripts/predict_autonomous_ct.py'),
                                    '--request', str(request_path)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True, env=dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK='0', OMP_NUM_THREADS='2'))
        try:
            def check_space():
                require(shutil.disk_usage(Path(log_path).parent).free >= free_floor_bytes, 'Output storage floor reached')
            return watch(process, seconds=seconds, rss_bytes=rss_bytes, tick=check_space)
        except Exception as exc:
            exc.resources = getattr(process, 'duration_resources', None)
            raise


def score_predictions(plan, plan_pin, journal_path):
    from src.inference.saved_prediction_scoring import score_saved
    from src.inference.evaluation_summary import summarize
    journal = [json.loads(line) for line in Path(journal_path).read_text().splitlines()]
    ids = [case['case_id'] for case in plan['cases']]
    require([row['case_id'] for row in journal] == ids and all(row['plan_sha256'] == plan_pin for row in journal),
            'Journal must account for the exact pinned plan, in order')
    rows = []
    for case, run in zip(plan['cases'], journal):
        row = dict(case_id=case['case_id'], inference_resources=run.get('resources'),
                   worker_failure=run.get('worker_result') if run['status'] == 'failed' else None, ct_sha256=case['ct']['sha256'],
                   reference_sha256={role: case['references'][role]['sha256'] for role in ('pancreas', 'lesion')},
                   reference_state=case['reference_state'], flags=case['flags'],
                   inference_status=run['status'], scoring_status='failed')
        try:
            request = prediction_request(plan, case, run.get('directory', '/unused'))
            require(run['request_identity'] == request_identity(request), 'Journal request identity differs')
            require(run['status'] in ('complete', 'reused'), 'No completed prediction; retained in denominator')
            result = verify_prediction(run['directory'], request, run['result_sha256'])
            refs = case['references']
            score = score_saved(Path(run['directory']) / 'prediction.nii.gz', refs['pancreas']['path'], refs['lesion']['path'],
                                expected_prediction_sha256=result['prediction_sha256'],
                                expected_pancreas_sha256=refs['pancreas']['sha256'], expected_lesion_sha256=refs['lesion']['sha256'],
                                allow_unknown_reference_units=refs['allow_unknown_units'])
            require(case['reference_state'] in ('unknown', score['lesion_reference_state']), 'Declared reference state differs')
            row.update(scoring_status='complete', score=score)
        except Exception as exc:
            row.update(error_type=type(exc).__name__, error=str(exc), inference_error=run.get('error'))
        rows.append(row)
    summary = summarize(rows, ids)
    complete = [r for r in rows if r['scoring_status'] == 'complete']
    values = [r['score']['metrics']['pancreas_parenchyma']['dice'] for r in complete
              if r['score']['metrics']['pancreas_parenchyma']['dice'] is not None]
    summary['pancreas_parenchyma_macro_dice'] = dict(value=sum(values)/len(values) if values else None, n=len(values))
    summary.update(fixed_reference_states=dict(Counter(c['reference_state'] for c in plan['cases'])),
                   unscored_reference_states=dict(Counter(r['reference_state'] for r in rows if r['scoring_status'] != 'complete')))
    return dict(component='fixed-cohort-evaluation-v1', cohort_id=plan['cohort_id'], plan_sha256=plan_pin,
                inference=plan['inference'], limitations=plan['limitations'], rows=rows, summary=summary)


def compare_reports(baseline, candidate):
    ids = [r['case_id'] for r in baseline['rows']]
    require(baseline['cohort_id'] == candidate['cohort_id'] and ids == [r['case_id'] for r in candidate['rows']]
            and len(ids) == len(set(ids)), 'Same complete ordered cohort required')
    rows = []
    for a, b in zip(baseline['rows'], candidate['rows']):
        require(a['ct_sha256'] == b['ct_sha256'] and a['reference_sha256'] == b['reference_sha256'] and
                a['reference_state'] == b['reference_state'], 'Paired source/reference identity differs')
        row = dict(case_id=a['case_id'], baseline_status=a['scoring_status'], candidate_status=b['scoring_status'],
                   flags=sorted(set(a['flags'] + b['flags'])), paired=False,
                   baseline_error=a.get('error'), candidate_error=b.get('error'),
                   baseline_inference_error=a.get('inference_error'), candidate_inference_error=b.get('inference_error'))
        if a['scoring_status'] == b['scoring_status'] == 'complete':
            require(a['score']['lesion_reference_state'] == b['score']['lesion_reference_state'], 'Paired reference state differs')
            row.update(paired=True, reference_state=a['score']['lesion_reference_state'], deltas={},
                       baseline_metrics=a['score']['metrics'], candidate_metrics=b['score']['metrics'])
            for metric, keys in (('lesion', ('dice', 'recall', 'false_positive_ml')),
                                 ('pancreas_parenchyma', ('dice',)), ('pancreas_lesion_union', ('dice',))):
                for key in keys:
                    x, y = a['score']['metrics'][metric][key], b['score']['metrics'][metric][key]
                    require((x is None) == (y is None), 'Paired metric definition differs')
                    row['deltas'][metric + '.' + key] = y - x if x is not None else None
        rows.append(row)
    pairs = [r for r in rows if r['paired']]
    positive = [r for r in pairs if r['reference_state'] == 'positive']
    paired_means = {}
    for key in ('lesion.dice', 'lesion.recall', 'pancreas_lesion_union.dice',
                'pancreas_parenchyma.dice', 'lesion.false_positive_ml'):
        metric, field = key.split('.')
        group = ([r for r in pairs if r['reference_state'] == 'reference_empty']
                 if key == 'lesion.false_positive_ml' else pairs)
        paired_means[key] = {}
        for arm in ('baseline', 'candidate'):
            values = [r[arm + '_metrics'][metric][field] for r in group
                      if r[arm + '_metrics'][metric][field] is not None]
            paired_means[key][arm] = dict(value=sum(values)/len(values) if values else None, n=len(values))
    return dict(paired_means=paired_means, fixed_cases=len(rows), complete_pairs=len(pairs), unpaired_cases=len(rows)-len(pairs), rows=rows,
                positive_pairs=len(positive), improved_positive_cases=sum(r['deltas']['lesion.dice'] > 1e-6 for r in positive),
                worsened_positive_cases=sum(r['deltas']['lesion.dice'] < -1e-6 for r in positive),
                tied_positive_cases=sum(abs(r['deltas']['lesion.dice']) <= 1e-6 for r in positive),
                baseline_plan_sha256=baseline['plan_sha256'], candidate_plan_sha256=candidate['plan_sha256'],
                limitations=['Paired scored cases only; unpaired failures remain visible',
                             'Development comparison, not untouched-test performance',
                             'Check model selection and controlled config differences separately'])
