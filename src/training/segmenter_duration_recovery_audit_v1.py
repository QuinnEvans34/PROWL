"""Bounded metadata for existing recovery predicates; never changes acceptance."""
import json
import math
import os
from pathlib import Path
from uuid import uuid4
import torch

COMPONENTS = ('model', 'optimizer', 'progress', 'cpu_rng', 'mps_rng')
MAX_PATHS = 16
MAX_BYTES = 32 * 1024


def encode(report):
    raw = json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) > MAX_BYTES:
        raise ValueError('Recovery audit exceeds metadata envelope')
    return raw


def publish(path, report):
    """Publish complete JSON exclusively; clean only this call's own temporary file."""
    from src.operations.artifact_store import directory, member_name
    path = Path(path); member_name(path.name); raw = encode(report)
    fd = directory(path.parent)
    temporary = 'audit-staging-' + uuid4().hex
    created = False
    try:
        child = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        created = True
        with os.fdopen(child, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, path.name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
        os.fsync(fd)
    finally:
        if created: os.unlink(temporary, dir_fd=fd); os.fsync(fd)
        os.close(fd)


def _key(value):
    if type(value) not in (str, int):
        raise ValueError('Unsupported recovery state key')
    return str(value)[:96]


def _tensor_details(a, b):
    row = dict(kind='tensor', actual_shape=list(a.shape), expected_shape=list(b.shape),
               actual_dtype=str(a.dtype), expected_dtype=str(b.dtype),
               actual_device=str(a.device), expected_device=str(b.device),
               mismatched_elements=None, max_absolute_difference=None,
               nonfinite_actual=None, nonfinite_expected=None)
    if a.layout != torch.strided or b.layout != torch.strided:
        raise ValueError('Unsupported recovery tensor layout')
    if a.shape != b.shape:
        return row
    x, y = a.detach().cpu().reshape(-1), b.detach().cpu().reshape(-1)
    mismatch = bad_x = bad_y = 0
    maximum = 0.0
    overflow = False
    # Bound temporary comparison allocations; reports never contain state values.
    for offset in range(0, x.numel(), 4096):
        u, v = x[offset:offset + 4096], y[offset:offset + 4096]
        mismatch += int(torch.count_nonzero(u != v).item())
        good_u, good_v = torch.isfinite(u), torch.isfinite(v)
        bad_x += int(torch.count_nonzero(~good_u).item())
        bad_y += int(torch.count_nonzero(~good_v).item())
        good = good_u & good_v
        if bool(good.any()):
            dtype = torch.complex128 if (u.is_complex() or v.is_complex()) else torch.float64
            delta = (u[good].to(dtype) - v[good].to(dtype)).abs()
            value = float(delta.max().item())
            overflow |= not math.isfinite(value)
            if math.isfinite(value):
                maximum = max(maximum, value)
    row.update(mismatched_elements=mismatch, max_absolute_difference=None if overflow else maximum,
               nonfinite_actual=bad_x, nonfinite_expected=bad_y, difference_overflow=overflow)
    return row


def compare(actual, expected, *, tree_equal):
    """Use the caller's unchanged tree predicate and ordinary progress equality."""
    if set(actual) != set(COMPONENTS) or set(expected) != set(COMPONENTS):
        raise ValueError('Recovery audit requires all five components')
    predicates = {name: bool(actual[name] == expected[name]) if name == 'progress'
                  else bool(tree_equal(actual[name], expected[name])) for name in COMPONENTS}
    differences = []
    components = {}

    def walk(a, b, path, depth=0):
        if tree_equal(a, b):
            return 0
        if depth >= 24:
            detail = dict(kind='depth_limit')
        elif isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor):
            detail = _tensor_details(a, b)
        elif isinstance(a, dict) and isinstance(b, dict):
            total = 0
            for key in sorted(set(a) | set(b), key=lambda k: (type(k).__name__, _key(k))):
                child = (path + '.' + _key(key))[:192]
                if key not in a or key not in b:
                    if len(differences) < MAX_PATHS:
                        differences.append(dict(path=child, kind='missing_field',
                                                actual_present=key in a, expected_present=key in b))
                    total += 1
                else:
                    total += walk(a[key], b[key], child, depth + 1)
            return total
        elif type(a) is type(b) and type(a) in (list, tuple) and len(a) == len(b):
            return sum(walk(x, y, (path + '.' + str(n))[:192], depth + 1)
                       for n, (x, y) in enumerate(zip(a, b)))
        else:
            detail = dict(kind='scalar_or_structure', actual_type=type(a).__name__[:64],
                          expected_type=type(b).__name__[:64])
            if type(a) in (int, float) and type(b) in (int, float):
                delta = abs(a - b)
                detail['max_absolute_difference'] = delta if math.isfinite(delta) else None
        if detail['kind'] == 'tensor' and detail['mismatched_elements'] is not None:
            statistics['mismatched_elements'] += detail['mismatched_elements']
            statistics['nonfinite_actual'] += detail['nonfinite_actual']
            statistics['nonfinite_expected'] += detail['nonfinite_expected']
        elif detail['kind'] != 'tensor' or detail['mismatched_elements'] is None:
            statistics['structural_or_scalar_fields'] += 1
        delta = detail.get('max_absolute_difference')
        if delta is not None:
            statistics['max_absolute_difference'] = max(statistics['max_absolute_difference'], delta)
        if len(differences) < MAX_PATHS:
            differences.append(dict(path=path, **detail))
        return 1

    for name in COMPONENTS:
        statistics = dict(max_absolute_difference=0.0, mismatched_elements=0,
                          nonfinite_actual=0, nonfinite_expected=0, structural_or_scalar_fields=0)
        count = 0 if predicates[name] else walk(actual[name], expected[name], name)
        components[name] = dict(exact=predicates[name], differing_fields=count, **statistics)
    report = dict(schema_version='segmenter-duration-recovery-audit-1',
                  all_exact=all(predicates.values()), components=components,
                  differing_fields=sum(v['differing_fields'] for v in components.values()),
                  differences=differences,
                  paths_truncated=sum(v['differing_fields'] for v in components.values()) > len(differences))
    encode(report)
    return report


def failure(*, phase, error, counts, restored, deltas, native, component_audit):
    if type(phase) is not str or len(phase) > 80:
        raise ValueError('Invalid cold failure phase')
    if set(counts) != {'forwards', 'optimizer_calls'} or any(type(v) is not int or v < 0 for v in counts.values()):
        raise ValueError('Invalid cold attempted counters')
    if type(restored) is not int or not 0 <= restored <= 128 or len(deltas) > 5 or len(native) > 25:
        raise ValueError('Invalid cold failure inventory')
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in deltas):
        raise ValueError('Invalid cold probability differences')
    rows = []
    for row in native:
        if set(row) != {'study_id', 'step', 'prediction_exact'} or type(row['study_id']) is not str or len(row['study_id']) > 96 or type(row['step']) is not int or type(row['prediction_exact']) is not bool:
            raise ValueError('Invalid cold native metadata')
        rows.append(dict(row))
    report = dict(schema_version='segmenter-duration-cold-failure-1', state='failed',
                  phase=phase, error_type=type(error).__name__[:80], model_calls=dict(counts),
                  completed_restores=restored, probability_max_differences=list(deltas),
                  completed_native_checks=rows, component_audit=component_audit,
                  recovery_qualified=False)
    encode(report)
    return report
