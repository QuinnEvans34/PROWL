"""Read-only source/cache metadata preparation; no arrays, GPU or training."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.segmenter_varied_region_v1 import planned_visits,coverage_slots
from src.data.verifier_generator_inputs_v1 import GeneratorInputs
from scripts.diagnostics import setup_fast_varied as parent

BASE=Path('E:/PROWL/readiness/verifier-generator-20261023-a01')
OUT=BASE/'restricted-inputs-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    import torch
    if torch.cuda.is_available():raise ValueError('CPU-only environment required')
    torch.set_num_threads(1)
    if OUT.exists():raise ValueError('Stage exists; do not rerun')
    partfile=BASE/'partitions.json';part=read(partfile)
    if sha(partfile)!='e70e110078d59d35b4171a9711bd2e0ea1ffa9f25aaf405e0d010f31e030fd35':raise ValueError('Partition changed')
    names=part['roles']['generator_train'];focus,exposure=planned_visits(names)
    old=parent.provider(prefetch=False)
    try:oldpin=old.pin
    finally:old.close()
    p=GeneratorInputs(partitions=part,partition_sha256=sha(partfile),focused_counts=focus,expected_parent_pin=oldpin,
        target_cache=parent.CACHE,cache_manifest_sha256=sha(parent.CACHE/'manifest.json'),
        planned_counts=read(parent.varied.SETUP/'schedule.json')['focused_counts'],manifest=parent.parent.MANIFEST,
        review=parent.parent.SOURCE_SETUP/'cohort-review.json',train_file=parent.parent.TRAIN,
        dev_file=parent.parent.SOURCE_SETUP/'development.txt')
    pins={};bank_total=0
    try:
        for n in names:
            f=parent.CACHE/(n+'.json');m=read(f);pins[str(f)]=sha(f)
            if pins[str(f)]!=p.cache_manifest['members'][n]['metadata_sha256']:raise ValueError('Cache metadata changed')
            coverage_slots(focus[n],len(m['cover']));bank_total+=len(m['cover'])
        for role,ids in part['roles'].items():
            if role=='generator_train':continue
            for n in ids:
                try:p.plan_next((n,0,0,42))
                except ValueError:pass
                else:raise ValueError('Reserved lookahead admitted')
        for n in part['development']:
            try:p.check_role(n,'validation','evaluator')
            except ValueError:pass
            else:raise ValueError('Development admitted')
        OUT.mkdir()
        result=dict(status='CPU_METADATA_PREPARED_NOT_LAUNCH_READY',train=800,reserved=533,development=70,
            updates=sum(exposure.values()),focus=sum(focus.values()),context=sum(exposure.values())-sum(focus.values()),
            reserved_bank_visits=bank_total,min_exposure=min(exposure.values()),max_exposure=max(exposure.values()),
            focused_counts=focus,exposure=exposure,control=p.control,control_sha256=p.pin,parent_control_sha256=oldpin,
            partition_sha256=sha(partfile),metadata_pins=pins,CT_reads=0,mask_reads=0,GPU_updates=0,
            geometry='existing81/43/71mm; user-approved design-informed exploratory',scientific_launch_authorized=False)
        with (OUT/'setup.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2)
        print(json.dumps({k:result[k] for k in ('status','train','reserved','development','updates','focus','context','reserved_bank_visits','min_exposure','max_exposure','control_sha256')}))
    finally:p.close()
if __name__=='__main__':main()
