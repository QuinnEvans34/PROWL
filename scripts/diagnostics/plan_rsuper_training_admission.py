"""Read-only metadata projection for the authorized R-Super KD launch preparation."""
import json
import math
from pathlib import Path
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.data.segmenter_teacher_geometry_v2 import metadata_grid,plan

def main():
    out=BASE/'rsuper-training-admission-01';out.mkdir(exist_ok=False)
    root=BASE/'metadata-received-01';train=(root/'membership/train.txt').read_text().split()
    dev=(root/'membership/development.txt').read_text().split()
    assert len(train)==len(set(train))==1333 and len(dev)==len(set(dev))==70 and not set(train)&set(dev)
    pilot=BASE/'rsuper-merlin-pilot-01';result=json.loads((pilot/'result.json').read_text())
    resources=json.loads((pilot/'resources.json').read_text());assert resources['success'] and resources['workers_reaped']
    pins={str(p):sha(p) for p in [Path(__file__),root/'membership/train.txt',root/'membership/development.txt',pilot/'result.json',pilot/'resources.json']}
    rows=[]
    for name in train:
        path=root/f'native-region/members/{name}.json';m=json.loads(path.read_text());pins[str(path)]=sha(path)
        grid=metadata_grid(m['parent_geometry']);tiles=plan(grid['shape'],max_voxels=256000000,max_tiles=10000)['tiles']
        rows.append(dict(case_id=name,tiles=tiles,raw_probability_bytes=math.prod(m['geometry']['shape'])*2))
    tiles=sum(r['tiles'] for r in rows);raw=sum(r['raw_probability_bytes'] for r in rows)
    measured_bytes=sum(r['cache_bytes'] for r in result['cases'])
    pilot_raw=sum(math.prod(json.loads((root/f'native-region/members/{r["case_id"]}.json').read_text())['geometry']['shape'])*2 for r in result['cases'])
    report=dict(status='PREPARATION_NOT_TRAINING',training_authorized=True,storage=storage_preflight(),train_count=len(train),dev_count=len(dev),teacher_targets_available=12,teacher_targets_required=len(train),estimated_tiles=tiles,raw_probability_bytes=raw,pilot_compressed_bytes=measured_bytes,pilot_raw_bytes=pilot_raw,extrapolated_compressed_bytes=raw*measured_bytes/pilot_raw,extrapolated_teacher_seconds=tiles*resources['seconds']/result['total_tiles'],projection_limit='Fixed selected pilot is not an unbiased sample; extrapolation is not a runtime guarantee.',remaining=['full local source binding','complete admitted teacher targets','real-data MPS zero-KD and positive-KD qualification','independent backup and cold restore','native evaluation qualification','frozen matched control and KD launch receipts'],cases=rows,pins=pins)
    write(out/'result.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','pins')},indent=2),flush=True)
if __name__=='__main__':main()
