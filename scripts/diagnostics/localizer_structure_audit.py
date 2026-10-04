"""D-314 one-shot prediction-only component audit. No inference or source references."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import resource
import signal
import sys
import time
import nibabel as nib
import numpy as np
import scipy
from src.training.localizer_structure_audit import analyze, recall_bounds
from src.data.source_inventory_records import require

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'outputs/prowl/LOCALIZER-STRUCTURE-AUDIT-20261001'
TRAIN_CODES = (150, 756, 6110, 6822, 7604, 7684)
SOURCES = {
 '010': ('CAP-EXP-010-review-20261001', '4055ed5addbac03f06f3f6c6ac973b6170fe1975f1e6a46d952ad29aad3e88c1',
         'twomm-training-a2593f26-59b6-4582-947d-582bfed6928f-execution', '84a16cc4e39409140404e8639daead08abce7fce9fee9f400effdccef548eee8'),
 '012': ('CAP-EXP-012-review-20261001', '9f69df5f1d80acf845f89fde52fa6cc4b06a5ca9ac9a78f055b3e8be097e78a6',
         'twomm-training-a0636d70-2ea5-4e5f-9167-db28bff562ba-execution', '2ca47e685f28d8007c34db51410482dc77b5b34da56598f4a645314ef1991926'),
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def safe_path(root, relative):
    root = Path(root)
    rel = Path(relative)
    require(not rel.is_absolute() and '..' not in rel.parts and bool(rel.parts), 'Unsafe relative path')
    path = root / rel
    require(path.resolve().is_relative_to(root.resolve()) and
            all(not p.is_symlink() for p in [path, *path.parents]), 'Unsafe symlink/path')
    require(path.is_file(), 'Missing retained input')
    return path


def checked(root, relative, pin):
    path = safe_path(root, relative)
    require(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Retained bytes changed')
    return path


def runtime():
    return dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                nibabel=nib.__version__, machine=platform.machine())


def code_pins():
    return {name: sha(REPO/name) for name in
            ('scripts/diagnostics/localizer_structure_audit.py', 'src/training/localizer_structure_audit.py')}


def read_sources():
    items = []
    for experiment, (review_name, review_pin, execution_name, execution_pin) in SOURCES.items():
        review = REPO/'outputs/prowl'/review_name; execution = REPO/'outputs/prowl'/execution_name
        require(sha(review/'receipt.json') == review_pin and sha(execution/'receipt.json') == execution_pin,
                'Trusted receipt changed')
        rr = json.loads((review/'receipt.json').read_text()); er = json.loads((execution/'receipt.json').read_text())
        require(rr['state'] == er['state'] == 'complete', 'Incomplete retained package')
        records = json.loads(checked(review, 'all-cases.json', rr['files']['all-cases.json']).read_text())
        selected = [r for r in records if r['step'] == 300 and (r['role'] == 'evaluator' or
                    (r['role'] == 'optimizer' and int(r['study_id'].split('_')[-1]) in TRAIN_CODES))]
        validate_selection(selected)
        for row in selected:
            relative = f"attempt/evaluation-0300/{row['role']}-{row['index']:04d}.json"
            record_path = checked(execution, relative, er['files'][relative])
            require(json.loads(record_path.read_text()) == row, 'Review/native row differs')
            mask_relative = relative.removesuffix('.json') + '.nii.gz'
            pin = er['files'][mask_relative]
            require(row['filename'] == Path(mask_relative).name and row['export']['sha256'] == pin['sha256'] and
                    row['export']['bytes'] == pin['bytes'], 'Export/receipt mismatch')
            checked(execution, mask_relative, pin)
            items.append(dict(experiment=experiment, row=row,
                mask=str((execution/mask_relative).relative_to(REPO)), pin=pin,
                record=str(record_path.relative_to(REPO)), record_pin=er['files'][relative]))
    for role in ('evaluator', 'optimizer'):
        sides = [{r['row']['study_id'] for r in items if r['experiment'] == exp and r['row']['role'] == role}
                 for exp in SOURCES]
        require(sides[0] == sides[1], 'Paired membership differs')
    for i in range(46):
        a, b = items[i]['row'], items[i+46]['row']
        require((a['study_id'], a['role'], a['index'], a['transform'], a['descriptor_sha256']) ==
                (b['study_id'], b['role'], b['index'], b['transform'], b['descriptor_sha256']), 'Paired geometry/identity differs')
    return items


def validate_selection(rows):
    require(len(rows) == 46 and all(r['step'] == 300 for r in rows), 'Wrong audit stage/count')
    require(len({(r['role'], r['study_id']) for r in rows}) == 46, 'Duplicate audit member')
    require(sum(r['role'] == 'evaluator' for r in rows) == 40 and
            {int(r['study_id'].split('_')[-1]) for r in rows if r['role'] == 'optimizer'} == set(TRAIN_CODES),
            'Wrong audit roles/membership')


def dump(path, data):
    with Path(path).open('x') as f: json.dump(data, f, indent=2, sort_keys=True, allow_nan=False); f.write('\n')


def consume(path, pin):
    dump(Path(path)/'started.json', dict(request_sha256=pin, state='consumed', started=time.time()))


def prepare():
    items = read_sources()
    request = dict(schema_version='localizer-structure-request-1', decision='D-314', sources=SOURCES,
        items=items, code=code_pins(), runtime=runtime(), array_reads=92,
        compressed_array_bytes=sum(i['pin']['bytes'] for i in items),
        expanded_array_bytes=sum(math.prod(i['row']['transform']['source_shape']) for i in items),
        limits=dict(seconds=1200, rss_bytes=8*1024**3, output_bytes=50*1024**2),
        original_array_reads=0, model_updates=0, policy_state='diagnostic_only')
    dump(OUT/'request.json', request)
    print(json.dumps(dict(request_sha256=sha(OUT/'request.json'), arrays=92,
        compressed_bytes=request['compressed_array_bytes'], expanded_bytes=request['expanded_array_bytes'])), flush=True)


def execute(expected):
    started = time.monotonic()
    path = OUT/'request.json'; require(sha(path) == expected, 'Exact request changed')
    request = json.loads(path.read_text())
    require(request['code'] == code_pins() and request['runtime'] == runtime(), 'Audit source/runtime changed')
    require(request['sources'] == {k:list(v) for k,v in SOURCES.items()} and
            request['items'] == read_sources(), 'Exact retained scope changed')
    run = OUT/'execution'; run.mkdir(exist_ok=False)
    consume(run, expected)
    allowed = {str((REPO/i['mask']).resolve()) for i in request['items']}
    # Enforce the no-source/no-model scope even if later audit code accidentally opens a record URI.
    def block(event, args):
        if event != 'open' or not isinstance(args[0], (str, bytes)): return
        p = Path(args[0]).resolve()
        require(not str(p).startswith('/Volumes/') and not p.is_relative_to(Path.home()/'PROWL-Backups'),
                'Original/backup reads forbidden')
        if str(p).endswith(('.nii', '.nii.gz', '.pt', '.pth')):
            require(str(p) in allowed, 'Unrequested array/model read forbidden')
    sys.addaudithook(block)
    results = []; array_bytes = expanded = 0
    def budget():
        require(time.monotonic()-started <= request['limits']['seconds'], 'Time budget exceeded')
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS ru_maxrss is bytes; Linux is KiB.
        peak *= 1 if sys.platform == 'darwin' else 1024
        require(peak <= request['limits']['rss_bytes'], 'RSS budget exceeded')
        require(sum(p.stat().st_size for p in run.iterdir() if p.is_file()) <= request['limits']['output_bytes'],
                'Output budget exceeded')
    def deadline(signum, frame):
        raise TimeoutError('Hard time budget exceeded')
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(max(1, math.floor(request['limits']['seconds']-(time.monotonic()-started))))
    try:
        for index, item in enumerate(request['items']):
            row = item['row']; result = dict(experiment=item['experiment'], role=row['role'],
                study_id=row['study_id'], index=row['index'], step=300, input_sha256=item['pin']['sha256'])
            try:
                budget(); mask = checked(REPO, item['mask'], item['pin'])
                image = nib.load(mask); transform = row['transform']
                require(list(image.shape) == transform['source_shape'] and image.get_data_dtype() == np.dtype('uint8')
                        and image.header.get_xyzt_units()[0] == 'mm' and
                        np.array_equal(image.affine, np.asarray(transform['source_affine'], dtype=np.float32).astype(float)),
                        'Native geometry/type differs')
                array_bytes += item['pin']['bytes']; expanded += math.prod(image.shape)
                require(array_bytes <= request['compressed_array_bytes'] and expanded <= request['expanded_array_bytes'],
                        'Exact read budget exceeded')
                p = np.asanyarray(image.dataobj)
                detail = analyze(p, image.affine, heartbeat=budget); del p, image
                require(detail['foreground_voxels'] == row['export']['foreground'], 'Foreground pin differs')
                require(detail['union_margin_box']['bounds'] == row['metrics']['box'] and
                        abs(detail['union_margin_box']['scan_fraction']-row['metrics']['scan_fraction']) < 1e-12,
                        'Retained union metric differs')
                result.update(state='complete', structure=detail, retained_metrics=row['metrics'],
                              hypothetical_largest_recall_bound=recall_bounds(detail, row['metrics']))
            except Exception as error:
                result.update(state='failed', error=f'{type(error).__name__}: {error}')
            dump(run/f'{index:03d}.json', result); results.append(result)
            print(f"{index+1}/92 {item['experiment']} {row['role']} {row['study_id']} {result['state']}", flush=True)
            if result['state'] == 'failed':
                # Leave all unconsumed members explicit; do not quietly drop a resource failure.
                for j, pending in enumerate(request['items'][index+1:], index+1):
                    record=dict(experiment=pending['experiment'],role=pending['row']['role'],study_id=pending['row']['study_id'],
                                state='not_run_after_failure')
                    dump(run/f'{j:03d}.json', record); results.append(record)
                raise RuntimeError('Audit incomplete; failed and not-run members retained')
        require(array_bytes == request['compressed_array_bytes'] and expanded == request['expanded_array_bytes'],
                'Read accounting differs')
        budget()
        dump(run/'results.json', results)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform == 'darwin' else 1024)
        dump(run/'receipt.json', dict(state='complete', request_sha256=expected, arrays=len(results),
            original_array_reads=0, model_updates=0, seconds=time.monotonic()-started, peak_rss_bytes=peak,
            compressed_array_bytes=array_bytes, expanded_array_bytes=expanded,
            files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in run.iterdir() if p.is_file()}))
    except Exception as error:
        dump(run/'failed.json', dict(state='failed', error=str(error), seconds=time.monotonic()-started))
        raise
    finally:
        signal.alarm(0)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare','execute'])
    parser.add_argument('--request-sha256'); args=parser.parse_args()
    if args.mode == 'prepare': prepare()
    else: execute(args.request_sha256)

if __name__ == '__main__': main()
