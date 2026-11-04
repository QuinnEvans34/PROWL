"""Metadata-only, exclusive partition export. No CT/model/GPU or launch path."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.verifier_partition_v1 import partition

OUT=Path('E:/PROWL/readiness/verifier-generator-20261023-a01')
BUNDLE=Path('E:/PROWL/transfer/mac-kd-metadata-20261023-a01')
def main():
    if OUT.exists():raise ValueError('Preparation already exists; do not rerun')
    pins={}
    def read(p):
        b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
    train=read(BUNDLE/'membership/train.txt').decode().split()
    dev=read(BUNDLE/'membership/development.txt').decode().split()
    if len(train)!=1333 or len(dev)!=70:raise ValueError('Unexpected cohort')
    manifest=json.loads(read(BUNDLE/'native-region/cache-manifest.json'))
    rows=[]
    for n in train:
        p=BUNDLE/'native-region/members'/(n+'.json');b=read(p)
        if pins[str(p)]!=manifest['members'][n]['metadata_sha256']:raise ValueError('Metadata changed')
        m=json.loads(b);a=m['geometry']['affine']
        determinant=(a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])-a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])+a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))
        rows.append(dict(case_id=n,positive=m['positive'],lesion_volume_mm3=m['lesion_voxels']*abs(determinant),source_sha256=m['source_sha256']))
    result=partition(rows,dev)
    for p in [Path(__file__),ROOT/'src/training/verifier_partition_v1.py']:read(p)
    result['input_pins']=pins
    result['scope']='New generator optimization/checkpoint exposure excluded; inherited preprocessing and pretraining provenance remain separate gates'
    result['scientific_launch_authorized']=False
    OUT.mkdir(parents=True,exist_ok=False)
    for name,value in [('partitions.json',result),('training-strata.json',rows)]:
        with (OUT/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2)
    for role,names in result['roles'].items():
        with (OUT/(role+'.txt')).open('x') as f:f.write('\n'.join(names)+'\n')
    print(json.dumps({'output':str(OUT),'counts':result['counts'],'partition_sha256':hashlib.sha256((OUT/'partitions.json').read_bytes()).hexdigest()}))
if __name__=='__main__':main()
