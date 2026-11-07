"""Bind exact train/dev roles to restored CTs and retained target geometry."""
import argparse,csv,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
import nibabel as nib
from src.data.stunet_inputs_20261106 import sha,stat
from src.data.segmenter_content_v1 import target_content
from src.data.segmenter_native_windows_v1 import geometry,orient,tiles
from src.data.segmenter_pancreas_region_v1 import crop_case
from src.data.segmenter_physical_windows_v1 import physical_geometry


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--output',required=True);p.add_argument('--qualification-only',action='store_true');a=p.parse_args()
    out=Path(a.output);out.mkdir(exist_ok=False);start=time.monotonic();E=Path('E:/PROWL')
    request_path=E/'readiness/stunet-source-restoration-20261106-a01/request.json'
    source_request=json.loads(request_path.read_text());sources=source_request['cases']
    restore=Path(source_request['output']);restored=None
    if not a.qualification_only:
        resources=json.loads((restore/'resources.json').read_text())
        if not resources['success'] or not resources['workers_reaped']:raise ValueError('Restoration must complete/reap')
        restored=json.loads((restore/'restoration.json').read_text())['cases']
        if set(restored)!=set(sources):raise ValueError('Incomplete restoration')
    else:
        events=[json.loads(x) for x in (restore/'progress.jsonl').read_text().splitlines()]
        if not any(x['event']=='reuse_verified' and x['cases']==479 for x in events):raise ValueError('Existing-source hash audit not complete')
    plan=json.loads(Path(a.plan).read_text());cache=E/'cache/varied-targets-20261022-a01'
    dev_request_path=E/'artifacts/week05-autonomous70-20261103-a03/request.json'
    dev_request=json.loads(dev_request_path.read_text());dev={c['case_id']:c for c in dev_request['cases']}
    rows={r['case_id']:r for r in csv.DictReader((E/'readiness/data-setup-20261010-a01/pants-manifest.csv').open())}
    config=dict(version='stunet-inputs128-1',qualification_only=a.qualification_only,plan=str(Path(a.plan)),plan_sha256=sha(a.plan),target_cache=str(cache),
                development=list(dev),sources={},native_profile={},source_request_sha256=sha(request_path),
                dev_request_sha256=sha(dev_request_path),scope='exploratory_provided_pancreas_region',
                normalization='unchanged HU[-100,250] to[0,1]',spacing='unchanged integer native-cell subdivision to <=1mm, no downsampling',
                input_units_policy='Inherited qualified PanTS physical geometry; not a new explicit-unit benchmark admission',
                excluded_from_development=sorted(n for n,r in rows.items() if r['protected_role']=='development' and n not in dev))
    for name,row in sources.items():
        path=Path(restored[name]['path']) if restored is not None else Path(row['existing_path']) if row['existing_path'] else None
        ct=dict(path=str(path) if path else None,stat=stat(path) if path else None,sha256=row['sha256'])
        if path and ct['stat']['bytes']!=row['bytes']:raise ValueError('CT size changed')
        if name in plan['members']:
            if plan['members'][name]['source_sha256']['ct']!=row['sha256'] or row['role']!='train':raise ValueError('Train CT/target identity')
            m=json.loads((cache/(name+'.json')).read_text());native=m['parent_geometry']
            config['sources'][name]={'ct':ct,'native_shape':native['source_shape'],'native_affine':native['source_affine']}
        elif name in dev:
            if row['role']!='development':raise ValueError('Protected development role')
            c=dev[name];config['sources'][name]={'ct':ct,'native_shape':c['expected_native']['shape'],'native_affine':c['expected_native']['affine']}
        else:raise ValueError('Unknown role')
        if path:
            header=nib.load(path);s=config['sources'][name]
            if header.shape!=tuple(s['native_shape']) or not np.allclose(header.affine,s['native_affine'],atol=1e-5,rtol=0):raise ValueError('CT header mismatch: '+name)
    for name,c in dev.items():
        entry=config['sources'][name];parent=geometry(entry['native_shape'],entry['native_affine']);masks={}
        for kind in ('pancreas','lesion'):
            path=Path(c['files'][kind]);expected=c['identity']['source_sha256'][kind]
            if sha(path)!=expected:raise ValueError('Development target identity')
            entry[kind]=dict(path=str(path),stat=stat(path),sha256=expected);obj=nib.load(path)
            if obj.shape!=tuple(entry['native_shape']) or not np.allclose(obj.affine,entry['native_affine'],atol=1e-5,rtol=0):raise ValueError('Development target alignment')
            masks[kind],_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
        target=orient(masks['pancreas'],parent).astype(np.uint8);target[orient(masks['lesion'],parent)!=0]=2
        case=crop_case(dict(name=name,target=target,geometry=parent,positive=bool(masks['lesion'].any()),original_pancreas=masks['pancreas']))
        if np.count_nonzero(case['target'])!=np.count_nonzero(target) or int((case['target']==2).sum())!=int(masks['lesion'].sum()):raise ValueError('Development coverage failed: '+name)
        record=physical_geometry(case['geometry']);config['native_profile'][name]=dict(tiles=len(tiles(record['shape'],window=128,stride=64)),positive=case['positive'],region_shape=case['geometry']['shape'],physical_shape=record['shape'])
    if len(config['sources'])!=1403 or len(config['development'])!=70:raise ValueError('Cohort count')
    config['preparation_seconds']=time.monotonic()-start
    with (out/'inputs.json').open('x') as f:json.dump(config,f)
    print(json.dumps(dict(status='PASS',qualification_only=a.qualification_only,available_cts=sum(x['ct']['path'] is not None for x in config['sources'].values()),
        native_tiles=sum(x['tiles'] for x in config['native_profile'].values()),native_cases=len(dev),
        native_positive=sum(x['positive'] for x in config['native_profile'].values()),seconds=config['preparation_seconds'])),flush=True)


if __name__=='__main__':main()
