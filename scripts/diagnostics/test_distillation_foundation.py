"""Bounded synthetic CPU tests only; never infer, cache CTs, or launch training."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.operations.full_training_platform import watch_windows

FILES = (
    'src/training/segmenter_distillation_v1.py',
    'src/data/segmenter_teacher_targets_v1.py',
    'tests/test_segmenter_distillation_v1.py',
    'tests/test_segmenter_teacher_targets_v1.py',
    'scripts/diagnostics/test_distillation_foundation.py',
)
EVIDENCE = Path('E:/PROWL/readiness')


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def run(attempt):
    if not attempt.isascii() or not attempt.isdecimal() or len(attempt) != 2:
        raise ValueError('Use a new two-digit development test attempt')
    output = EVIDENCE / ('distillation-foundation-20261023-a' + attempt)
    output.mkdir(exist_ok=False)
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FILES}
    write(output / 'request.json', dict(scope='synthetic CPU unit tests only',
        pins=pins, seconds=120, rss_bytes=2 * 1024**3, cuda_visible_devices='',
        scientific=False, ct_reads=0, test_set_reads=0, teacher_inferences=0))
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
        MKL_NUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               *FILES[2:4], '--junitxml', str(output / 'tests.xml')]
    success = False
    error = None
    with (output / 'worker.log').open('x', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=environment,
            stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            watch_windows(process, seconds=120, rss_bytes=2 * 1024**3)
            success = True
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
        finally:
            resources = dict(getattr(process, 'duration_resources', {}),
                success=success, exit_code=process.returncode, error=error)
            write(output / 'resources.json', resources)
    suites = []
    if (output / 'tests.xml').exists():
        suites = [dict(node.attrib) for node in ET.parse(output / 'tests.xml').iter('testsuite')]
    result = dict(success=success, suites=suites, resources=resources,
        source_pins_unchanged=all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
                                  for p, h in pins.items()),
        synthetic_only=True, scientific_updates=0, ready_for_training=False)
    write(output / 'result.json', result)
    print(json.dumps(dict(output=str(output), **result), indent=2))
    return 0 if success and result['source_pins_unchanged'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', required=True)
    raise SystemExit(run(parser.parse_args().attempt))
