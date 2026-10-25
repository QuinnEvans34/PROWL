"""CPU-only admission rehearsal on a snapshot of completed teacher cases."""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE, write, storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from scripts.diagnostics.prepare_rsuper_full_provider import provider
OUT = BASE/'rsuper-target-admission-20261025-01'
TARGETS = BASE/'rsuper-full-targets-02'


def worker():
    from src.data.segmenter_generated_target_admission_v1 import admit
    from src.data.pants_errata_v1 import EXPECTED
    request = json.loads((OUT/'request.json').read_text())
    for path, pin in request['pins'].items():
        if sha(Path(path)) != pin: raise ValueError('Admission input changed')
    p, _, _ = provider()
    expected = json.loads((BASE/'rsuper-full-provider-20261025-02/result.json').read_text())
    if p.pin != expected['provider_sha256']: raise ValueError('Qualified provider changed')
    producer = json.loads((TARGETS/'request.json').read_text())
    rows = {n: json.loads((TARGETS/(n+'.json')).read_text()) for n in request['cases']}
    manifest, common = admit(TARGETS, producer, dict(members=rows), {}, p, qualification_only=True)
    # Removing confirmed false lesion labels must not invalidate teacher image grids.
    for name in EXPECTED:
        _, corrected = p.cache_member(name)
        original = json.loads((BASE/f'metadata-received-01/native-region/members/{name}.json').read_text())
        if (corrected['geometry'] != original['geometry']
                or corrected['parent_geometry'] != original['parent_geometry']
                or corrected['source_sha256']['ct'] != original['source_sha256']['ct']):
            raise ValueError('Errata teacher geometry differs')
    write(OUT/'qualification-manifest.json', manifest)
    write(OUT/'result.json', dict(success=True, cases=request['cases'],
        provider_sha256=p.pin, corrected_geometries_verified=len(EXPECTED),
        ct_voxel_reads=0, gpu_updates=0, scientific_ready=False,
        scope='partial completed-output admission rehearsal only', common_identity=common))


if __name__ == '__main__':
    if '--worker' in sys.argv: worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight(); OUT.mkdir(exist_ok=False)
        progress = [json.loads(line) for line in (TARGETS/'progress.jsonl').read_text().splitlines()]
        names = [r['case_id'] for r in progress]
        files = [Path(__file__).resolve(), ROOT/'src/data/segmenter_generated_target_admission_v1.py',
                 ROOT/'scripts/diagnostics/prepare_rsuper_full_provider.py', TARGETS/'request.json',
                 BASE/'rsuper-full-provider-20261025-02/result.json']
        files += [TARGETS/(n+suffix) for n in names for suffix in ('.json', '.npz')]
        write(OUT/'request.json', dict(cases=names, pins={str(p): sha(p) for p in files},
                                     seconds=600, rss_bytes=2*1024**3))
        if not run([sys.executable, __file__, '--worker'], OUT, seconds=600,
                   rss_bytes=2*1024**3, env=dict(os.environ, CUDA_VISIBLE_DEVICES='-1', OMP_NUM_THREADS='1')):
            raise SystemExit(1)
