"""Reuse recorded boxes: freeze generator-only margins, then audit reserved boxes."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.verifier_generator_geometry_v1 import fit_margin,apply_margin,contains

BASE=Path('E:/PROWL/readiness/verifier-generator-20261023-a01')
BUNDLE=Path('E:/PROWL/transfer/mac-kd-metadata-20261023-a01')
OUT=BASE/'geometry-01'
def main():
    if OUT.exists():raise ValueError('Existing stage; do not rerun')
    pins={}
    def read(p):
        b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
    partitions=json.loads(read(BASE/'partitions.json'))
    if pins[str(BASE/'partitions.json')]!='e70e110078d59d35b4171a9711bd2e0ea1ffa9f25aaf405e0d010f31e030fd35':raise ValueError('Partition changed')
    review=json.loads(read(BUNDLE/'membership/cohort-review.json'))
    inventory_path=Path('E:/PROWL/readiness/training-coverage-inventory-20261018-a01/cases.jsonl')
    inventory={r['case_id']:r for r in map(json.loads,read(inventory_path).splitlines())}
    def record(n):
        p=BUNDLE/'source/cached-metadata'/(n+'.json');m=json.loads(read(p))
        if pins[str(p)]!=review['prepared_cache']['members'][n]['metadata_sha256']:raise ValueError('Metadata changed')
        positive=review['target_states'][n]=='positive'
        if positive:
            r=inventory[n]
            if r['source_lesion_sha256']!=m['source_sha256']['lesion']:raise ValueError('Lesion identity changed')
            lesion=r['lesion_box']
        else:lesion=None
        t=m['transform'];return dict(native_box=t['native_box'],shape=t['source_shape'],affine=t['source_affine'],lesion_box=lesion)
    names=partitions['roles']['generator_train'];records={n:record(n) for n in names}
    margins=fit_margin(records,names)
    OUT.mkdir()
    def write(name,v):
        with (OUT/name).open('x') as f:json.dump(v,f,sort_keys=True,indent=2)
    write('frozen-margin.json',dict(margins=margins,fit_patients=names,input_pins=dict(pins),selection='generator800_only_max_source_plane_extension_ceil_plus1mm',uses_reserved_labels=False))
    # Freeze is written BEFORE reserved-patient assessment; failures never refit it.
    checks={}
    for role,ids in partitions['roles'].items():
        failed=[]
        for n in ids:
            r=records[n] if n in records else record(n)
            box=apply_margin(r['native_box'],r['shape'],r['affine'],margins)
            if not contains(box,r['lesion_box']):failed.append(n)
        checks[role]=dict(cases=len(ids),clipped_lesion_boxes=failed)
    write('coverage-assessment.json',dict(checks=checks,pins=pins,test_reads=0,CT_reads=0,mask_reads=0,development_reads=0,margin_refit=False))
    print(json.dumps(dict(margins=margins,checks=checks,output=str(OUT))))
if __name__=='__main__':main()
