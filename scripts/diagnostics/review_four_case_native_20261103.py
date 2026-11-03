"""CPU-only review of eight retained predictions, exact schema inventory and safe packet."""
import sys,json,hashlib,shutil,time,subprocess,os,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import evaluate_four_case_exception_20261102 as b
OUT=Path('E:/PROWL/readiness/week05-native-review-20261103-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/week05-native-review-20261103-a01')
PIN='f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd'

def schema(value):
    if value is None:return {'type':'null'}
    if isinstance(value,bool):return {'type':'boolean'}
    if isinstance(value,(float,int)):return {'type':'number'}
    if isinstance(value,str):return {'type':'string'}
    if isinstance(value,list):
        unique={json.dumps(schema(v),sort_keys=True):schema(v) for v in value}
        return dict(type='array',items=next(iter(unique.values())) if len(unique)==1 else {'anyOf':list(unique.values())} if unique else {})
    return dict(type='object',properties={k:schema(v) for k,v in value.items()},required=list(value),additionalProperties=False)

def run():
    import nibabel as nib
    import numpy as np
    from src.inference.native_review_overlays_20261103 import canonical,selected_component,sheet
    import jsonschema
    started=time.monotonic();r=b.request(PIN);b.q.resource_gate()
    for p in b.BASE.rglob('*'):
        if p.is_file() and b.q.sha(p)!=b.q.sha(b.BACKUP/p.relative_to(b.BASE)):raise ValueError('Prior backup mismatch: '+str(p))
    if any(PIN in (p.info.get('cmdline') or []) and '--run-sha256' in (p.info.get('cmdline') or []) for p in __import__('psutil').process_iter(['cmdline'])):raise RuntimeError('Prior owner still active')
    images=[];records={};bindings={};predictions={}
    for name in ['PanTS_00004681','PanTS_00006755','PanTS_00000909','PanTS_00002028']:
        case=next(c for c in r['cases'] if c['case_id']==name);files=case['files'];ctn=nib.load(files['ct']);ct=np.asarray(ctn.dataobj,dtype=np.float32)
        pan=np.asarray(nib.load(files['pancreas']).dataobj,bool);les=np.asarray(nib.load(files['lesion']).dataobj,bool)
        ct,aff,transform=canonical(ct,ctn.affine)
        pan=canonical(pan,ctn.affine)[0];les=canonical(les,ctn.affine)[0];arms={};scores={};results={};targets=[]
        bound={k:dict(path=v,sha256=b.q.sha(v)) for k,v in files.items()}
        for arm in b.ARMS:
            d=b.BASE/name/arm;result=json.loads((d/'result.json').read_text());score=json.loads((d/'score.json').read_text())
            predn=nib.load(d/'prediction.nii.gz')
            if predn.shape!=ctn.shape or not np.allclose(predn.affine,ctn.affine,atol=1e-5,rtol=0):raise ValueError('Prediction geometry mismatch')
            native=np.asarray(predn.dataobj,dtype=np.uint8);arms[arm]=canonical(native,ctn.affine)[0];scores[arm]=score;results[arm]=result
            bound[arm]={k:dict(path=str(d/(k+'.json')),sha256=b.q.sha(d/(k+'.json'))) for k in ['result','score','input-access']}
            bound[arm]['prediction']=dict(path=str(d/'prediction.nii.gz'),sha256=b.q.sha(d/'prediction.nii.gz'))
            for key,value in [('result',result),('evidence',result['evidence']),('score',score)]:
                records.setdefault(arm+'-'+key,[]).append(value)
        if name in ['PanTS_00004681','PanTS_00006755']:
            ids=sorted({x['component_id'] for arm in b.ARMS for x in scores[arm]['lesion_components']['reference'] if not x['any_overlap']})
            native_les=np.asarray(nib.load(files['lesion']).dataobj,bool)
            for i in ids:
                row=next(x for x in scores['autonomous']['lesion_components']['reference'] if x['component_id']==i)
                targets.append(('missed-reference-'+str(i),canonical(selected_component(native_les,row),ctn.affine)[0],dict(kind='missed_reference',component=row)))
        else:
            for arm in b.ARMS:
                rows=[x for x in scores[arm]['lesion_components']['predicted'] if not x['any_overlap']]
                row=sorted(rows,key=lambda x:(-x['volume_ml'],x['component_id']))[0]
                native=np.asarray(nib.load(b.BASE/name/arm/'prediction.nii.gz').dataobj,dtype=np.uint8)
                targets.append((arm+'-largest-fp',canonical(selected_component(native==2,row),ctn.affine)[0],dict(kind='largest_false_positive_by_volume_then_id',source_arm=arm,component=row)))
        for label,selected,target in targets:
            image,choices=sheet(ct,pan,les,arms,selected,aff,name+' | '+label)
            path=OUT/(name+'-'+label+'.png');image.save(path)
            images.append(dict(path=path.name,sha256=b.q.sha(path),case_id=name,target=target,planes=choices,source_bindings=bound,models=r['models'],display=dict(window=[-100,250],orientation='lossless closest RAS; no resampling of source arrays',affine=aff.tolist(),transform=transform.tolist())))
        bindings[name]=bound
        if time.monotonic()-started>600 or b.q.tree_bytes(OUT)>1024**3:raise RuntimeError('Review resource cap')
    schemas={}
    for key,values in records.items():
        unique={json.dumps(schema(v),sort_keys=True):schema(v) for v in values};spec={'$schema':'https://json-schema.org/draft/2020-12/schema','anyOf':list(unique.values())}
        for value in values:jsonschema.validate(value,spec)
        schemas[key]=spec
    b.q.write(OUT/'observed-record-schemas.json',dict(version='observed-physical-executor-schema-1',schemas=schemas,note='Exact observed keys/types, not a new producer schema; nullable and empty component variants retained'))
    b.q.write(OUT/'review-manifest.json',dict(version='native-four-case-review-1',request_sha256=PIN,original_summary_sha256=b.q.sha(b.BASE/'summary.json'),images=images,bindings=bindings,seconds=time.monotonic()-started,model_forwards=0,training=False,clinical_review=False))
    # Initial portable importer packet: only2028 fits the requested32M voxel limit.
    case=next(c for c in r['cases'] if c['case_id']=='PanTS_00002028');d=b.BASE/case['case_id']/'autonomous'
    packet_files={'request.json':b.BASE/'request.json','result.json':d/'result.json','prediction.nii.gz':d/'prediction.nii.gz','input-access.json':d/'input-access.json','ct.nii.gz':Path(case['files']['ct'])}
    if np.prod(case['header']['ct']['shape'])>32_000_000:raise ValueError('Importer voxel cap')
    if any(packet_files[n].stat().st_size>64*1024**2 for n in ['ct.nii.gz','prediction.nii.gz']):raise ValueError('Importer file cap')
    manifest=dict(schema='prowl-review-transfer-v1',files=[dict(path=k,bytes=p.stat().st_size,sha256=b.q.sha(p)) for k,p in packet_files.items()])
    if sum(x['bytes'] for x in manifest['files'])>512*1024**2 or len(manifest['files'])>127:raise ValueError('Packet cap')
    b.q.write(OUT/'transfer-manifest.json',manifest);archive=OUT/'review-2028-autonomous.tar'
    with tarfile.open(archive,'x') as tar:
        for name,path in {**packet_files,'transfer-manifest.json':OUT/'transfer-manifest.json'}.items():
            if path.is_symlink():raise ValueError('Symlink not allowed')
            tar.add(path,arcname=name,recursive=False)
    if archive.stat().st_size>256*1024**2:raise ValueError('Archive cap')
    with tarfile.open(archive,'r') as tar:
        expected={x['path']:x for x in manifest['files']};seen=[]
        for member in tar:
            if not member.isfile() or '/' in member.name or '\\' in member.name:raise ValueError('Unsafe packet member')
            raw=tar.extractfile(member).read();seen.append(member.name)
            if member.name!='transfer-manifest.json':
                if len(raw)!=expected[member.name]['bytes'] or hashlib.sha256(raw).hexdigest()!=expected[member.name]['sha256']:raise ValueError('Packet readback')
        if set(seen)!=set(expected)|{'transfer-manifest.json'} or len(seen)!=len(set(seen)):raise ValueError('Packet completeness')
    b.q.write(OUT/'packet-receipt.json',dict(path=str(archive),bytes=archive.stat().st_size,sha256=b.q.sha(archive),manifest=manifest,transmitted=False))

if __name__=='__main__':
    if '--worker' in sys.argv:run()
    else:
        if OUT.exists() or BACKUP.exists():raise FileExistsError('Review already started; no overwrite')
        b.q.resource_gate();OUT.mkdir();b.q.write(OUT/'request.json',dict(version='bounded-native-review-1',seconds=600,rss_bytes=12*1024**3,output_bytes=1024**3,source_request_sha256=PIN,code_sha256={str(p):b.q.sha(p) for p in [Path(__file__),ROOT/'src/inference/native_review_overlays_20261103.py']}))
        try:b.q.supervise([sys.executable,__file__,'--worker'],log=OUT/'worker.log',seconds=600,rss_bytes=12*1024**3,tick=b.q.resource_gate)
        finally:
            if b.q.tree_bytes(OUT)>1024**3:raise RuntimeError('Review output cap')
            shutil.copytree(OUT,BACKUP)
            for p in OUT.rglob('*'):
                if p.is_file() and b.q.sha(p)!=b.q.sha(BACKUP/p.relative_to(OUT)):raise ValueError('Review backup mismatch')
