"""Original-native counts/components and closed scoring evidence; no model."""
from io import BytesIO
import json,math
import numpy as np
from scipy import ndimage
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_content_v1 as content
TASK='segmenter_original_native_scoring_v1'
CLASSES={'pancreas_parenchyma':[1],'lesion':[2],'pancreas_lesion_union':[1,2]}
MAX_VOXELS=46_219_264


def decode_prediction(raw,shape):
    b=BytesIO(raw);require(np.lib.format.read_magic(b)==(1,0),'Native NPY format')
    s,f,d=np.lib.format.read_array_header_1_0(b,max_header_size=512)
    require(s==tuple(shape) and len(s)==3 and math.prod(s)<=MAX_VOXELS and d==np.dtype('uint8') and not f and len(raw)==b.tell()+math.prod(s),'Native prediction allocation/grid differs')
    a=np.load(BytesIO(raw),allow_pickle=False);require(np.isin(a,[0,1,2]).all(),'Wrong native codes');return a


def from_confusion(matrix):
    require(isinstance(matrix,list) and len(matrix)==3 and all(isinstance(r,list) and len(r)==3 and all(type(v)==int and v>=0 for v in r) for r in matrix),'Invalid integer confusion matrix')
    m=np.asarray(matrix,np.int64);metrics={}
    for name,cls in CLASSES.items():
        n=int(m[cls,:].sum());p=int(m[:,cls].sum());tp=int(m[np.ix_(cls,cls)].sum())
        metrics[name]=dict(target_voxels=n,predicted_voxels=p,true_positive=tp,dice=2*tp/(n+p) if n else None,recall=tp/n if n else None)
    return metrics


def score(prediction,pancreas,lesion,*,target_state,tick=lambda:None):
    p=np.asarray(prediction);a=np.asarray(pancreas);b=np.asarray(lesion)
    require(target_state in ('positive','verified_negative') and p.shape==a.shape==b.shape and p.ndim==3 and p.size<=MAX_VOXELS and np.isin(p,[0,1,2]).all() and np.isin(a,[0,1]).all() and np.isin(b,[0,1]).all(),'Invalid native grids/semantics')
    require(bool(b.any())==(target_state=='positive'),'Unknown or contradictory lesion target')
    matrix=np.zeros((3,3),np.int64);outside=0
    for z in range(0,p.shape[2],16):
        tick();ss=(slice(None),slice(None),slice(z,z+16));truth=np.where(b[ss],2,a[ss]).astype(np.uint8)
        matrix+=np.bincount((truth*3+p[ss]).ravel(),minlength=9).reshape(3,3);outside+=int(np.count_nonzero((b[ss]==1)&(a[ss]==0)))
    tick();labels,n=ndimage.label(b,structure=np.ones((3,3,3),np.uint8));sizes=np.zeros(n+1,np.int64);hits=np.zeros(n+1,np.int64)
    for z in range(0,p.shape[2],16):
        tick();ss=(slice(None),slice(None),slice(z,z+16));v=labels[ss];sizes+=np.bincount(v.ravel(),minlength=n+1);hits+=np.bincount(v[p[ss]==2],minlength=n+1)
    boxes=ndimage.find_objects(labels,max_label=n);components=[]
    for i,box in enumerate(boxes,1):
        tick();require(box is not None,'Missing native component')
        components.append(dict(component_id=i,native_voxels=int(sizes[i]),true_positive=int(hits[i]),recall=float(hits[i]/sizes[i]),missed=bool(hits[i]==0),bounds_xyz_half_open=[[s.start,s.stop] for s in box],source_boundary_contact=any(s.start==0 or s.stop==p.shape[k] for k,s in enumerate(box))))
    matrix=matrix.tolist();r=dict(confusion_matrix=matrix,metrics=from_confusion(matrix),outside_pancreas_voxels=outside,connectivity=26,components=components)
    require(sum(c['native_voxels'] for c in components)==r['metrics']['lesion']['target_voxels'] and sum(c['true_positive'] for c in components)==r['metrics']['lesion']['true_positive'],'All component accounting differs')
    require(len(canonical(r))<=16*1024**2,'Complete component evidence exceeds resource budget; no truncation');return r


def aggregates(scores):
    result={}
    for role in ('train','validation'):
        rows=[s for s in scores if s['protected_role']==role]
        if not rows:continue
        matrix=np.sum([np.asarray(r['confusion_matrix'],np.int64) for r in rows],axis=0).tolist()
        result[role]=dict(cases=len(rows),pooled_confusion_matrix=matrix,pooled=from_confusion(matrix),macro={name:{k:float(np.mean([r['metrics'][name][k] for r in rows if r['metrics'][name][k] is not None])) if any(r['metrics'][name][k] is not None for r in rows) else None for k in ('dice','recall')} for name in CLASSES},reference_components=sum(len(r['components']) for r in rows),missed_components=sum(c['missed'] for r in rows for c in r['components']))
    return result


def check_targets(descriptor,rows):
    require(len(rows)==2 and {r['kind'] for r in rows}=={'pancreas','lesion'} and len({r['uri'] for r in rows})==2,'Exact target-only pair required')
    for r in rows:
        ref=descriptor[r['kind']]
        require(r['study_id']==descriptor['study_id'] and r['protected_role']==descriptor['protected_role'] and ref['root_alias']=='followup_source' and ref['uri']==r['uri'] and ref['bytes']==r['compressed_bytes']==r['observation']['bytes'] and ref['content_sha256']==r['sha256'] and r['geometry']==descriptor['geometry'],'Targets differ from qualified descriptor')


def read_targets(rootfd,descriptor,rows,counts,limits,tick=lambda:None):
    check_targets(descriptor,rows)
    for key,field in [('hash_bytes','compressed_bytes'),('decode_bytes','compressed_bytes'),('expanded_bytes','expanded_bytes')]:content.reserve(counts,key,sum(r[field] for r in rows),limits)
    from scripts.diagnostics import segmenter_source_verification as source
    arrays={};references=[]
    for row in rows:
        tick()
        with source.source_stream(rootfd,row) as stream:
            content.hash_exact(stream,row,counts,limits,tick);stream.seek(0);stored,header,read=content.decode_exact(stream,row,counts,limits,tick)
        mask,decoding=content.target_content(stored,header,tick);arrays[row['kind']]=mask
        references.append(dict(study_id=row['study_id'],protected_role=row['protected_role'],kind=row['kind'],uri=row['uri'],header=header,read=read,decoding=decoding,decoded_sha256=digest(mask.tobytes(order='C'))));del stored
    require(arrays['pancreas'].any() and bool(arrays['lesion'].any())==(descriptor['lesion_target_state']=='positive'),'Qualified native target changed')
    return arrays['pancreas'],arrays['lesion'],references


def validate_payload(files,identity):
    req=identity['request'];pin=identity['request_sha256']
    require(set(files)=={'request.json','scores.json','references.json','aggregates.json','production.json'} and files['request.json']==canonical(req) and digest(files['request.json'])==pin,'Scoring inventory/request differs')
    require(req['task']==TASK and req['stage']=='original_native_scoring' and req['model_updates_allowed'] is False and req['ct_reads_allowed'] is False,'Wrong scoring stage')
    scores=json.loads(files['scores.json']);refs=json.loads(files['references.json']);production=json.loads(files['production.json'])
    require(len(scores)==len(req['cases'])==7 and len(refs)==len(req['files'])==14,'Scoring case/reference inventory')
    for row,expected in zip(refs,req['files']):
        require(set(row)=={'study_id','protected_role','kind','uri','header','read','decoding','decoded_sha256'} and all(row[k]==expected[k] for k in ('study_id','protected_role','kind','uri')),'Reference scope drift')
        require(row['read']==dict(compressed_bytes=expected['compressed_bytes'],expanded_bytes=expected['expanded_bytes'],sha256=expected['sha256'],gzip_eof_crc_verified=True),'Original source accounting/hash drift')
        h=row['header'];g=expected['geometry'];require(h['shape']==g['shape_xyz'] and np.allclose(np.asarray(h['affine']).ravel(),g['affine_ras'],rtol=0,atol=1e-5),'Reference grid changed')
        scaling=expected['header'] if expected['kind']=='lesion' else expected['retained_content'];sc=dict(slope=scaling['effective_slope'],intercept=scaling['effective_intercept']) if expected['kind']=='lesion' else scaling['effective_scaling'];units=scaling['units']
        require(h['slope']==sc['slope'] and h['intercept']==sc['intercept'] and h['units']==units and h['offset']==352 and np.dtype(h['dtype'])==np.dtype(expected['dtype']) and np.allclose(h['spacing'],g['spacing_mm_xyz'],rtol=0,atol=1e-5),'Reference scaling/units/type/spacing drift')
        if expected['kind']=='lesion':require(h['header_sha256']==expected['header']['decompressed_header_sha256'],'Original lesion header drift')
        require(isinstance(row['decoded_sha256'],str) and len(row['decoded_sha256'])==64,'Missing decoded reference identity')
        dec=row['decoding'];require(dec['policy']==content.APPROVED_POLICY and dec['max_endpoint_residual']<=1e-6 and sum(p['count'] for p in dec['semantic_value_counts'])==math.prod(h['shape']) and all(p['count']>=0 and min(abs(p['semantic']),abs(p['semantic']-1))<=1e-6 for p in dec['semantic_value_counts']),'Reference binary decoding differs')
    for row,e,export in zip(scores,req['cases'],req['prediction_exports']):
        require(set(row)=={'study_id','protected_role','source_shape','source_affine','prediction_sha256','confusion_matrix','metrics','outside_pancreas_voxels','connectivity','components','oracle'},'Score fields differ')
        require(all(row[k]==e[k] for k in ('study_id','protected_role')) and row['source_shape']==e['descriptor']['geometry']['shape_xyz'] and row['source_affine']==np.asarray(e['descriptor']['geometry']['affine_ras']).reshape(4,4).tolist() and row['prediction_sha256']==export['native_sha256'],'Score image/role/grid provenance differs')
        m=from_confusion(row['confusion_matrix']);require(row['metrics']==m and sum(sum(v) for v in row['confusion_matrix'])==math.prod(row['source_shape']),'Score formula/voxel accounting differs')
        matrix=np.asarray(row['confusion_matrix'],np.int64);require(matrix.sum(0).tolist()==export['class_counts'],'Prediction counts drift')
        for name in CLASSES:require(m[name]['target_voxels']==e['fidelity']['metrics'][name]['native_voxels'],'Original target counts differ from retained accepted source evidence')
        pair=[v for v in refs if v['study_id']==row['study_id']];require(len(pair)==2 and next(v for v in pair if v['kind']=='lesion')['decoding']['foreground_voxels']==m['lesion']['target_voxels'] and next(v for v in pair if v['kind']=='pancreas')['decoding']['foreground_voxels']==m['pancreas_parenchyma']['target_voxels']+m['lesion']['target_voxels']-row['outside_pancreas_voxels'],'Decoded foreground/reference counts drift')
        require(row['outside_pancreas_voxels']==e['fidelity']['outside_pancreas_voxels'] and row['connectivity']==26 and len(row['components'])==e['fidelity']['source_component_count'],'Native component/reference relationship differs')
        for i,(c,old) in enumerate(zip(row['components'],e['fidelity']['components']),1):
            require(set(c)=={'component_id','native_voxels','true_positive','recall','missed','bounds_xyz_half_open','source_boundary_contact'} and c['component_id']==i and c['native_voxels']==old['native_voxels'] and type(c['true_positive']) is int and 0<=c['true_positive']<=c['native_voxels'] and c['recall']==c['true_positive']/c['native_voxels'] and c['missed']==(c['true_positive']==0),'Component identity/count/formula differs')
        for c in row['components']:
            b=c['bounds_xyz_half_open'];require(len(b)==3 and all(len(v)==2 and all(type(x)==int for x in v) and 0<=v[0]<v[1]<=row['source_shape'][i] for i,v in enumerate(b)) and c['source_boundary_contact']==any(v[0]==0 or v[1]==row['source_shape'][i] for i,v in enumerate(b)),'Component physical bounds drift')
        require(sum(c['native_voxels'] for c in row['components'])==m['lesion']['target_voxels'] and sum(c['true_positive'] for c in row['components'])==m['lesion']['true_positive'],'Components omitted or hits forged')
        require(row['oracle']['state']=='passed' and row['oracle']['confusion_matrix']==row['confusion_matrix'],'Independent confusion oracle differs')
    require(json.loads(files['aggregates.json'])==aggregates(scores),'Role aggregate drift')
    require(production['request_sha256']==pin and production['source_counts']=={k:req['limits'][k] for k in ('hash_bytes','decode_bytes','expanded_bytes')} and production['source_arrays_read']==14 and production['ct_arrays_read']==production['model_forwards']==production['model_updates']==0 and production['code_pins']==req['code_pins'] and production['runtime']==req['runtime'] and production['mount_before']==production['mount_after'],'Production/source/permission drift')
    return dict(task=TASK,request_sha256=pin,cases=7,references=14,model_updates=0,source_counts=production['source_counts'],aggregate_sha256=digest(files['aggregates.json']),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})
