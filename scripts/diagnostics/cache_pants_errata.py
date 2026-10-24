"""Build seven corrected target derivatives with bounded CPU work; no CT reads."""
import json
import os
from pathlib import Path
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE, write, storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import ARCHIVE_SHA, sha
from src.data.pants_errata_v1 import EXPECTED, VERSION
from src.data.pants_errata_cache_v1 import load_target
OVERLAY_SHA = '033f8f5cb7533031412a04f8daff62e5f95786123d0a21fc3c32c711ef5b06bc'
OUT = BASE / 'annotation-errata-cache-01'


def worker():
    if os.environ.get('PROWL_ERRATA_CACHE') != '1':
        raise ValueError('Supervisor required')
    import hashlib
    import numpy as np
    import nibabel as nib
    from copy import deepcopy
    from src.data.segmenter_content_v1 import target_content
    from src.data.segmenter_native_windows_v1 import orient
    from src.data.segmenter_fast_varied_v1 import save_target
    from src.data.segmenter_physical_windows_v1 import coverage_bank
    from src.data.segmenter_varied_region_v1 import components
    request = json.loads((OUT / 'request.json').read_text())
    for path, pin in request['pins'].items():
        assert sha(Path(path)) == pin, path
    overlay_path = BASE / 'annotation-errata-02/overlay.json'
    assert sha(overlay_path) == OVERLAY_SHA
    overlay = json.loads(overlay_path.read_text())
    rows = {r['case_id']: r for r in overlay['cases']}
    assert len(rows) == len(overlay['cases']) == 7 and set(rows) == set(EXPECTED)
    archive = BASE / 'mac-kd-metadata-20261023-a01.zip'
    assert sha(archive) == ARCHIVE_SHA
    members = {}
    with zipfile.ZipFile(archive) as z:
        handoff = json.loads(z.read('HANDOFF.json'))
        def read(name):
            raw = z.read(name)
            assert hashlib.sha256(raw).hexdigest() == handoff['files'][name]['sha256']
            return raw
        train = set(read('membership/train.txt').decode().splitlines())
        dev = set(read('membership/development.txt').decode().splitlines())
        assert set(rows) <= train and not set(rows) & dev
        for name, row in sorted(rows.items()):
            meta = json.loads(read(f'native-region/members/{name}.json'))
            original = Path(row['original_path'])
            corrected = Path(row['corrected_path'])
            pancreas = original.with_name('pancreas.nii.gz')
            assert sha(original) == row['original_sha256'] == meta['source_sha256']['lesion']
            assert sha(corrected) == row['corrected_sha256']
            assert sha(pancreas) == row['pancreas_sha256'] == meta['source_sha256']['pancreas']
            masks = {}
            for kind, path in [('pancreas', pancreas), ('lesion', corrected)]:
                obj = nib.load(path)
                assert list(obj.shape) == meta['parent_geometry']['source_shape']
                assert np.prod(obj.shape) <= 256000000
                assert np.allclose(obj.affine, meta['parent_geometry']['source_affine'], atol=1e-4, rtol=0)
                masks[kind], _ = target_content(obj.dataobj.get_unscaled(), dict(slope=float(obj.dataobj.slope), intercept=float(obj.dataobj.inter)))
            assert not masks['lesion'].any()
            sl = tuple(slice(lo, hi) for lo, hi in zip(meta['region_low'], meta['region_high']))
            target = np.ascontiguousarray(orient(masks['pancreas'], meta['parent_geometry'])[sl])
            assert int(target.sum()) == int(masks['pancreas'].sum()) == meta['pancreas_source_voxels']
            small = deepcopy(meta)
            small.update(name=name, positive=False, lesion_voxels=0, label_revision_sha256=OVERLAY_SHA,
                         original_source_sha256=meta['source_sha256'],
                         source_sha256={**meta['source_sha256'], 'lesion': row['corrected_sha256']})
            small['cover'] = coverage_bank(target > 0, small['record'])
            small['parts'], positive = components(target, small['record'])
            assert not positive
            sampling = json.loads(corrected.with_name('sampling.json').read_text())
            # JSON normalization handles tuples/NumPy scalars in generated metadata.
            from src.data.manifest_records import canonical
            assert canonical(small['cover']) == canonical(sampling['cover'])
            assert canonical(small['parts']) == canonical(sampling['parts'])
            members[name] = save_target(OUT, name, target, small)
            with np.load(OUT / (name + '.npz'), allow_pickle=False) as saved:
                assert np.array_equal(saved['target'], target)
            assert sha(original) == row['original_sha256'] and sha(pancreas) == row['pancreas_sha256']
            print(name, 'exact target roundtrip; pancreas preserved; zero lesions', flush=True)
    write(OUT / 'manifest.json', dict(version=VERSION, overlay_sha256=OVERLAY_SHA,
        members=members, complete=False, scope='seven_corrected_training_derivatives_only',
        scientific_launch_authorized=False, unaffected_cache_admitted=False))
    pin = sha(OUT / 'manifest.json')
    for name in sorted(rows):
        load_target(OUT, name, role='train', manifest_sha256=pin, overlay_sha256=OVERLAY_SHA)
    for path, original_pin in request['pins'].items():
        assert sha(Path(path)) == original_pin, path
    write(OUT / 'result.json', dict(success=True, cases=len(members), manifest_sha256=pin,
        cache_bytes=sum(m['bytes'] for m in members.values()), producing_pins_verified=len(request['pins']),
        ct_reads=0, model_runs=0, training_updates=0, full_provider_qualified=False))


if __name__ == '__main__':
    if '--worker' in sys.argv:
        worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight()
        OUT.mkdir(exist_ok=False)
        pins = dict(json.loads((BASE / 'annotation-errata-02/request.json').read_text())['pins'])
        for p in [Path(__file__).resolve(), ROOT / 'src/data/pants_errata_cache_v1.py']:
            pins[str(p)] = sha(p)
        write(OUT / 'request.json', dict(pins=pins, seconds=600, rss_bytes=12*1024**3,
            overlay_sha256=OVERLAY_SHA, scope='seven corrected target caches; no CT or model'))
        ok = run([sys.executable, __file__, '--worker'], OUT, seconds=600, rss_bytes=12*1024**3,
                 env={**os.environ, 'PROWL_ERRATA_CACHE':'1', 'OMP_NUM_THREADS':'2'})
        raise SystemExit(0 if ok else 1)
