"""CPU-only full-cohort binding and sampling-plan checks; no CT/model runs."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
OUT=BASE/'rsuper-full-provider-20261025-02'
SOURCES=BASE/'rsuper-training-sources-01'

def provider():
    from src.data.pants_errata_kd_inputs_v1 import ErrataKDInputs
    from src.data.segmenter_varied_region_v1 import planned_visits
    train=(SOURCES/'train.txt').read_text().split();counts,exposure=planned_visits(train)
    root=BASE/'metadata-received-01/native-region/members'
    names=train  # Development geometry is computed by the unchanged evaluator; no teacher metadata.
    p=ErrataKDInputs(native_metadata_root=root,native_metadata_pins={n:sha(root/(n+'.json')) for n in names},correction_root=BASE/'annotation-errata-cache-01',correction_manifest_sha256='77811d7b62a188d5644887b3ed52f7082ab95a6f576042ef87baac485e187c63',overlay_sha256='033f8f5cb7533031412a04f8daff62e5f95786123d0a21fc3c32c711ef5b06bc',manifest=SOURCES/'manifest.csv',review=SOURCES/'review.json',train_file=SOURCES/'train.txt',dev_file=SOURCES/'development.txt',planned_counts=counts)
    return p,counts,exposure

def worker():
    from src.data.segmenter_varied_region_v1 import coverage_slots
    from src.data.pants_errata_v1 import EXPECTED
    p,counts,exposure=provider();rows=[]
    for name in p.control['train']:
        _,m=p.cache_member(name);slots=coverage_slots(counts[name],len(m['cover']))
        rows.append(dict(case_id=name,positive=m['positive'],coverage_windows=len(slots),focused_visits=counts[name],total_visits=exposure[name],corrected=name in EXPECTED))
    assert len(rows)==1333 and sum(r['positive'] for r in rows)==664
    assert sum(counts.values())==18000 and sum(exposure.values())==24000
    assert len(p.control['validation'])==70 and not set(p.control['train'])&set(p.control['validation'])
    write(OUT/'control.json',p.control)
    write(OUT/'result.json',dict(success=True,provider_sha256=p.pin,train=1333,development=70,positive_train=664,focused_updates=18000,context_updates=6000,planned_updates=24000,ct_voxel_reads=0,optimizer_updates=0,rows=rows,scientific_ready=False,remaining='complete teacher manifest and actual full-provider MPS/executor/evaluator recovery'))

if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();OUT.mkdir(exist_ok=False)
        files=[Path(__file__).resolve(),ROOT/'src/data/pants_errata_kd_inputs_v1.py',ROOT/'src/training/segmenter_errata_kd_session_v1.py',SOURCES/'manifest.csv',SOURCES/'review.json',SOURCES/'metadata/control.json']
        write(OUT/'request.json',dict(pins={str(p):sha(p) for p in files},seconds=600,rss_bytes=2*1024**3))
        if not run([sys.executable,__file__,'--worker'],OUT,seconds=600,rss_bytes=2*1024**3,env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='1')):raise SystemExit(1)
