"""Configurable experiments on the existing trainer; preflight never opens image/weight payloads.

Scientific acceptance records are inputs, not produced by this module. Historical pilot
consumers retain their original contracts. No fixed cohort cardinality or update ceiling.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from copy import deepcopy
from pathlib import Path

import yaml

from src.utils.config import REPO_ROOT, load_config


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merge(base, overrides):
    result = deepcopy(base)
    for key, value in overrides.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else deepcopy(value)
    return result


def ids(path):
    values = Path(path).read_text().split()
    if not values or len(values) != len(set(values)):
        raise ValueError(f"Empty or duplicate cohort IDs: {path}")
    return values


def resolve(path, root=REPO_ROOT):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def load_experiment(path):
    spec = yaml.safe_load(Path(path).read_text())
    required = {'version', 'name', 'base_config', 'recipe', 'cohort', 'initialization', 'run'}
    if not isinstance(spec, dict) or set(spec) != required or spec['version'] != 1:
        raise ValueError('Expected experiment version 1 and its documented fields')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', spec['name']):
        raise ValueError('Experiment name must be a simple unique directory name')
    run = spec['run']
    if set(run) != {'max_updates', 'validate_every', 'checkpoint_every', 'log_every', 'cache', 'max_seconds', 'min_free_bytes'}:
        raise ValueError('Unknown or missing run setting')
    for key in ('max_updates', 'validate_every', 'checkpoint_every', 'log_every'):
        if type(run[key]) is not int or run[key] < 1:
            raise ValueError(f'{key} must be a positive integer')
    if run['validate_every'] > run['max_updates']:
        raise ValueError('Validation interval must not exceed training horizon')
    if run['cache'] not in ('none', 'ram', 'disk'):
        raise ValueError('Unsupported cache mode')
    for key in ('max_seconds', 'min_free_bytes'):
        if run[key] is not None and (type(run[key]) is not int or run[key] <= 0):
            raise ValueError(f'{key} must be a positive integer or null while planning')
    init = spec['initialization']
    if set(init) != {'kind', 'checkpoint', 'sha256', 'source_review'} or init['kind'] not in ('scratch', 'suprem'):
        raise ValueError('Explicit scratch or SuPreM initialization required')
    if init['kind'] == 'scratch' and any(init[k] is not None for k in ('checkpoint', 'sha256', 'source_review')):
        raise ValueError('Scratch cannot carry a weight source')
    if init['kind'] == 'suprem' and (not init['checkpoint'] or not re.fullmatch('[0-9a-f]{64}', init['sha256'] or '')):
        raise ValueError('SuPreM requires an explicit checkpoint and SHA-256')
    cohort = spec['cohort']
    if set(cohort) != {'manifest', 'train_ids', 'development_ids', 'original_train_ids', 'original_development_ids', 'test_ids', 'review'}:
        raise ValueError('Explicit cohort files and review required')
    cfg = merge(load_config(resolve(spec['base_config'])), spec['recipe'])
    if cfg.get('label_mode') != 'pancreas_lesion' or cfg['model']['out_channels'] != 3:
        raise ValueError('This adapter supports the three-class baseline; anatomy5 uses its paired protocol')
    if cfg.get('pancreas_resolver', 'combined') not in ('combined', 'hbt_union'):
        raise ValueError('Unsupported pancreas resolver')
    lr = cfg['optimizer']['lr_transfer' if init['kind'] == 'suprem' else 'lr_scratch']
    if not isinstance(lr, (int, float)) or not math.isfinite(lr) or lr <= 0:
        raise ValueError('Learning rate must be finite and positive')
    output = REPO_ROOT / 'outputs' / 'experiments' / spec['name']
    cfg['paths']['manifest'] = str(resolve(cohort['manifest']))
    cfg['paths']['output_dir'] = str(output)
    cfg['paths']['splits_dir'] = str(output / 'splits')
    cfg['paths']['pretrained_weights'] = str(resolve(init['checkpoint'])) if init['checkpoint'] else ''
    cfg['transfer']['use_pretrained'] = init['kind'] == 'suprem'
    cfg['training']['cache_dir'] = str(output / 'cache')
    cfg['mlflow']['tracking_uri'] = f"sqlite:///{output / 'mlflow.db'}"
    cfg['_experiment'] = spec
    return cfg


def preflight(cfg, *, inspect_payload_paths=False, source_review_mode='separation'):
    """Aggregate missing prerequisites. Path inspection is explicit; no payload decode/hash."""
    if source_review_mode not in ('separation', 'development_use'):
        raise ValueError('Unknown source review scope')
    spec = cfg['_experiment']; cohort = spec['cohort']; errors = []; groups = {}; pins = {}; source_limitations = []
    for key in ('train_ids', 'development_ids', 'original_train_ids', 'original_development_ids', 'test_ids'):
        try:
            path = resolve(cohort[key]); groups[key] = set(ids(path)); pins[key] = sha256(path)
        except (OSError, ValueError) as exc:
            errors.append(f'{key}: {exc}')
    if len(groups) == 5:
        train, dev = groups['train_ids'], groups['development_ids']
        if not train <= groups['original_train_ids']: errors.append('Training members outside original training role')
        if not dev <= groups['original_development_ids']: errors.append('Development members outside original development role')
        if train & dev or (train | dev) & groups['test_ids']: errors.append('Training/development/test overlap')
    try:
        path = resolve(cohort['manifest']); pins['manifest'] = sha256(path)
        with path.open(newline='') as stream: rows = list(csv.DictReader(stream))
        names = [r['case_id'] for r in rows]
        if len(names) != len(set(names)): errors.append('Duplicate manifest case IDs')
        by_id = {r['case_id']: r for r in rows}
        columns = ['ct_path', 'lesion_path'] + (['head_path', 'body_path', 'tail_path'] if cfg.get('pancreas_resolver') == 'hbt_union' else ['pancreas_path'])
        for name in sorted(groups.get('train_ids', set()) | groups.get('development_ids', set())):
            row = by_id.get(name)
            if row is None:
                errors.append(f'Missing manifest member: {name}'); continue
            for col in columns:
                value = row.get(col)
                if not value or not Path(value).is_absolute(): errors.append(f'{name}: missing/relative {col}')
                elif inspect_payload_paths and not Path(value).is_file(): errors.append(f'{name}: unavailable {col}')
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f'manifest: {exc}')
    # Reviews bind conclusions to the files actually selected, without re-running qualification.
    review_path = cohort['review']
    try:
        if not review_path: raise ValueError('Current cohort/label review is pending')
        review = json.loads(resolve(review_path).read_text())
        if review.get('decision') != 'accepted' or review.get('input_sha256') != pins or not review.get('evidence'):
            raise ValueError('Cohort review must accept these exact files and cite qualification evidence')
    except (OSError, ValueError) as exc: errors.append(str(exc))
    init = spec['initialization']
    if init['kind'] == 'suprem':
        try:
            if not init['source_review']: raise ValueError('SuPreM source/selection separation review is pending')
            review = json.loads(resolve(init['source_review']).read_text())
            expected = {k: pins.get(k) for k in ('original_train_ids', 'original_development_ids', 'test_ids')}
            accepted = review.get('decision') == 'accepted'
            if source_review_mode == 'development_use' and review.get('decision') == 'accepted_for_development':
                accepted = (review.get('evaluation_scope') == 'development_only' and
                            bool(review.get('user_instruction')) and bool(review.get('limitations')))
                source_limitations = review.get('limitations', [])
            if (not accepted or review.get('checkpoint_sha256') != init['sha256']
                    or review.get('protected_roles_sha256') != expected or not review.get('evidence')):
                raise ValueError('SuPreM review must bind checkpoint and protected roles and cite source evidence')
            if inspect_payload_paths and not resolve(init['checkpoint']).is_file(): errors.append('SuPreM checkpoint unavailable')
        except (OSError, ValueError) as exc: errors.append(str(exc))
    if any(spec['run'][k] is None for k in ('max_seconds', 'min_free_bytes')):
        errors.append('Concrete runtime/storage allocation is pending')
    if Path(cfg['paths']['output_dir']).exists(): errors.append('Output already exists; choose a new run name')
    return {'ready': not errors, 'errors': errors, 'input_sha256': pins,
            'train_cases': len(groups.get('train_ids', [])), 'development_cases': len(groups.get('development_ids', [])),
            'max_updates': spec['run']['max_updates'], 'payload_paths_checked': inspect_payload_paths,
            'source_review_mode': source_review_mode, 'source_limitations': source_limitations}


def apply_arguments(args, cfg):
    spec = cfg['_experiment']; run = spec['run']; cohort = spec['cohort']
    args.max_iters = run['max_updates']; args.val_every = run['validate_every']
    args.ckpt_every = run['checkpoint_every']; args.log_every = run['log_every']
    args.cache = run['cache']; args.run_name = spec['name']
    args.train_ids = str(resolve(cohort['train_ids'])); args.val_ids = str(resolve(cohort['development_ids']))
    args.scratch = spec['initialization']['kind'] == 'scratch'; args.transfer = not args.scratch


def prepare_run(cfg, report):
    if not report['ready'] or not report['payload_paths_checked']:
        raise ValueError('Successful preflight including source path availability is required')
    check_resources(cfg, elapsed=0)
    output = Path(cfg['paths']['output_dir']); output.mkdir(parents=True, exist_ok=False)
    (output / 'splits').mkdir()
    cohort = cfg['_experiment']['cohort']
    # Preserve exact metadata used by the run; later manifest edits cannot change its inputs.
    for key in ('train_ids', 'development_ids', 'original_train_ids', 'original_development_ids', 'test_ids', 'manifest'):
        raw = resolve(cohort[key]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != report['input_sha256'][key]:
            raise ValueError(f'Input metadata changed after preflight: {key}')
        destination = output / ('manifest.csv' if key == 'manifest' else f'splits/{key}.txt')
        destination.write_bytes(raw)
        if key in ('train_ids', 'development_ids', 'manifest'): cohort[key] = str(destination)
    (output / 'splits' / 'test.txt').write_bytes((output / 'splits' / 'test_ids.txt').read_bytes())
    cfg['paths']['manifest'] = cohort['manifest']
    for key, path in [('cohort-review', cohort['review']), ('source-review', cfg['_experiment']['initialization']['source_review'])]:
        if path: (output / f'{key}.json').write_bytes(resolve(path).read_bytes())
    (output / 'resolved.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False))
    (output / 'preflight.json').write_text(json.dumps(report, indent=2) + '\n')


def check_resources(cfg, *, elapsed):
    """Check at admission/update boundaries; not a hard watchdog for a hung kernel."""
    import shutil
    limits = cfg['_experiment']['run']
    if elapsed >= limits['max_seconds']:
        raise RuntimeError('Experiment runtime limit reached; durable checkpoints retained')
    directory = Path(cfg['paths']['output_dir'])
    while not directory.exists(): directory = directory.parent
    if shutil.disk_usage(directory).free < limits['min_free_bytes']:
        raise RuntimeError('Experiment free-space floor reached; durable checkpoints retained')


def record_event(cfg, **event):
    """Keep training/validation history even when optional MLflow logging is unavailable."""
    with (Path(cfg['paths']['output_dir']) / 'metrics.jsonl').open('a') as stream:
        stream.write(json.dumps(event, allow_nan=False) + '\n')


def load_suprem_checked(model, initialization):
    """Load only a fully matching backbone; preserve the freshly initialized task head."""
    import io
    import torch
    raw = resolve(initialization['checkpoint']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != initialization['sha256']:
        raise ValueError('SuPreM checkpoint hash mismatch')
    checkpoint = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True)
    state = checkpoint.get('net', checkpoint)
    if not isinstance(state, dict): raise ValueError('Expected a SuPreM state dictionary')
    normalized = {k.removeprefix('module.'): v for k, v in state.items()}
    expected = model.state_dict(); head = {'conv_final.2.conv.weight', 'conv_final.2.conv.bias'}
    if len(normalized) != len(state) or set(normalized) != set(expected) or not head <= set(expected):
        raise ValueError('Unexpected or missing SuPreM tensor names')
    for key, value in normalized.items():
        if not isinstance(value, torch.Tensor) or value.dtype != expected[key].dtype or not torch.isfinite(value).all():
            raise ValueError(f'Invalid SuPreM tensor: {key}')
        if key not in head and value.shape != expected[key].shape:
            raise ValueError(f'SuPreM backbone shape mismatch: {key}')
        if key in head and (value.shape[0] != 32 or value.shape[1:] != expected[key].shape[1:]):
            raise ValueError(f'Unexpected released SuPreM head: {key}')
    model.load_state_dict({k: expected[k] if k in head else v for k, v in normalized.items()}, strict=True)
