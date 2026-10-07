# Duration stage adapter; original v5 source remains fixed.
"""Fresh final-stage target scope; original arrays require the exact launch grant."""
from copy import deepcopy
import gzip,io,json,os
import nibabel as nib
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_content_v1 as content,segmenter_geometry_loader_v1 as loader,segmenter_training_inputs_v1 as inputs,segmenter_geometry_v1 as geometry
from src.training import segmenter_training_probe_v1 as prior,segmenter_native_scoring_v1 as scoring
from scripts.diagnostics import segmenter_source_verification as source

STAGE='segmenter_duration_native_targets_v1'
STEPS=(48,96,144,192)

def stage_scope(scope,step):
    require(type(step) is int and step in STEPS,'Unapproved native stage')
    cases=scope['cases'] if step==192 else scope['cases'][:6]
    ids={c['study_id'] for c in cases}
    files=[r for r in scope['files'] if r['study_id'] in ids]
    return dict(stage=STAGE,step=step,cases=cases,files=files,limits=scope['stage_limits'][str(step)])


def original_scope(cases,files,capability,metadata_pin):
    require(len(cases)==7 and len(files)==14 and len({r['uri'] for r in files})==14,'Exact fourteen-target scope')
    for c in cases:scoring.check_targets(c['descriptor'],[r for r in files if r['study_id']==c['study_id']])
    scope=dict(stage=STAGE,domain='original_native_targets',cases=deepcopy(cases),files=deepcopy(files),capability=deepcopy(capability),metadata_receipt_sha256=metadata_pin)
    scope['stage_limits']={str(step):{k:sum(r[f] for r in files if step==192 or r['study_id'] in {c['study_id'] for c in cases[:6]}) for k,f in [('hash_bytes','compressed_bytes'),('decode_bytes','compressed_bytes'),('expanded_bytes','expanded_bytes')]} for step in STEPS}
    scope['limits']={k:sum(v[k] for v in scope['stage_limits'].values()) for k in ('hash_bytes','decode_bytes','expanded_bytes')}
    scope['logical_target_reads']=50
    return scope

def validate_scope(scope,control):
    require(set(scope)=={'stage','domain','cases','files','capability','metadata_receipt_sha256','stage_limits','limits','logical_target_reads'} and scope['stage']==STAGE and scope['domain'] in ('original_native_targets','invented_native_targets'),'Wrong final reference stage/domain')
    cases=scope['cases'];rows=scope['files'];require(len(cases)==7 and len(rows)==14 and [c['study_id'] for c in cases]==control['train']+control['validation'] and len({r['uri'] for r in rows})==14,'Final reference membership')
    expected=original_scope(cases,rows,scope['capability'],scope['metadata_receipt_sha256'])
    require(type(scope['logical_target_reads']) is int and all(type(n) is int and n>=0 for v in [scope['limits']]+list(scope['stage_limits'].values()) for n in v.values()) and scope['limits']==expected['limits'] and scope['stage_limits']==expected['stage_limits'] and scope['logical_target_reads']==50 and all(v['expanded_bytes']<=700*1024**2 for v in scope['stage_limits'].values()),'Repeated native reference byte/read budget')
    require(scope['capability']['operations']==['full_compressed_hash','full_gzip_decode_native_targets'] and scope['capability']['source_writes'] is False and scope['capability']['global_activation'] is False,'Target-only source capability')
    for c in cases:
        require(c['protected_role']==('train' if c['study_id'] in control['train'] else 'validation') and c['descriptor']['lesion_target_state'] in ('positive','verified_negative'),'Reference role/target state')
        scoring.check_targets(c['descriptor'],[r for r in rows if r['study_id']==c['study_id']]);geometry.validate_record(c['transform'],c['transform_sha256'])
        require(c['transform']['source_identity']['study_id']==c['study_id'] and c['transform']['source_shape']==c['descriptor']['geometry']['shape_xyz'],'Reference source lineage')
        if control['domain']=='invented_arrays_only':expected_image=control['member_sha256'][c['study_id']]['image']
        else:
            from src.data.segmenter_cache_v1 import names
            expected_image=control['member_sha256'][names((control['train']+control['validation']).index(c['study_id']))['image']]
        require(c['image_sha256']==expected_image,'Reference/image source lineage')
        require(len(c['reference_components'])==c['fidelity']['source_component_count'],'Reference component inventory')

class RealTargets:
    def __init__(self,provider,request,grant):
        from src.training.segmenter_duration_executor_v1 import checked_grant,validate_request
        validate_request(request);checked_grant(request,grant)
        require(type(provider) is inputs.QualifiedInputs and canonical(provider.control)==request['controls']['inputs.json'].encode() and request['targets']['domain']=='original_native_targets','Unqualified original reference consumer')
        self.provider=provider;self.request=deepcopy(request);self.grant=grant;self.counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);self.used=set();self.stage_counts={str(n):dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0) for n in STEPS};self.mount_before=None;self.mount_after=None
    def read(self,session,sid,*,tick=lambda:None):
        from src.training.segmenter_duration_executor_v1 import checked_grant
        checked_grant(self.request,self.grant);r=self.request;scope=r['targets']
        require(session.identity==r['identity'] and session.step in STEPS and not session.dirty and (session.step,sid) not in self.used,'Premature/dirty/repeated original reference read')
        stage=stage_scope(scope,session.step);c=next((v for v in stage['cases'] if v['study_id']==sid),None);require(c is not None,'Absent final reference case');d=self.provider._session.select(sid,c['descriptor']['operation']);require(d==c['descriptor'] and self.provider._session.records==self.provider._binding['records'],'Original purpose/descriptor replay differs')
        before=source.mount_guard(scope['capability'])
        if self.mount_before is None:self.mount_before=before
        require(before==self.mount_before,'Original source mount drift');self.used.add((session.step,sid))
        with source.directory(scope['capability']['source_root']) as fd:
            s=os.fstat(fd);require((s.st_dev,s.st_ino)==(before['root_device'],before['root_inode']),'Wrong opened original root')
            counts=self.stage_counts[str(session.step)];before_counts=counts.copy()
            try:result=scoring.read_targets(fd,d,[v for v in stage['files'] if v['study_id']==sid],counts,stage['limits'],tick)
            finally:
                for key in self.counts:self.counts[key]+=counts[key]-before_counts[key]
                require(all(self.counts[k]<=scope['limits'][k] for k in self.counts),'Aggregate original-target envelope')
        self.mount_after=source.mount_guard(scope['capability']);require(self.mount_after==self.mount_before,'Original mount changed after targets');return result

def invented_arrays(negative=False):
    pan=np.zeros((512,402,197),np.uint8);les=np.zeros_like(pan);pan[100:281,120:261,:81]=1
    if not negative:les[180:182,200:202,:2]=1;les[240:242,210:212,20:22]=1;les[280:283,200:202,40:42]=1
    return pan,les

def invented_blob(array,kind):
    affine=np.diag([.78,.78,1.25,1.]);image=nib.Nifti1Image(array,affine);image.header.set_xyzt_units('mm');raw=image.to_bytes();blob=gzip.compress(raw,compresslevel=1,mtime=0)
    scale=dict(effective_slope=1.,effective_intercept=0.,units=['mm','unknown'],decompressed_header_sha256=digest(raw[:348])) if kind=='lesion' else dict(effective_scaling=dict(slope=1.,intercept=0.),units=['mm','unknown'])
    row=dict(kind=kind,compressed_bytes=len(blob),expanded_bytes=len(raw),sha256=digest(blob),dtype='uint8',geometry=dict(shape_xyz=list(array.shape),spacing_mm_xyz=[.78,.78,1.25],affine_ras=affine.ravel().tolist()),**({'header':scale} if kind=='lesion' else {'retained_content':scale}))
    return blob,row

class InventedTargets:
    def __init__(self,provider):
        require(type(provider) is inputs.InventedInputs and provider.size==144,'Invented MPS target domain required');self.provider=provider;self.blobs={};self.cases=[];self.files=[];self.counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);self.used=set();self.stage_counts={str(n):dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0) for n in STEPS};self.mount_before=self.mount_after=dict(domain='invented_bytes_no_original_sources')
        for negative in (False,True):
            pan,les=invented_arrays(negative);perfect=np.where(les,2,pan).astype(np.uint8);score=scoring.score(perfect,pan,les,target_state='verified_negative' if negative else 'positive')
            payload={kind:invented_blob(a,kind) for kind,a in [('pancreas',pan),('lesion',les)]};self.blobs[negative]=payload
            for sid in provider.control['train']+provider.control['validation']:
                is_negative=provider.control['target_metadata'][sid]['class_counts'][2]==0
                if is_negative!=negative:continue
                role='train' if sid in provider.control['train'] else 'validation';x=provider.get(sid,role=role,operation='inference').image;case=prior.native_case(x);t=geometry.plan_geometry([512,402,197],np.diag([.78,.78,1.25,1.]),[[100,120,0],[281,261,81]],geometry.recipe(),source_identity=dict(study_id=sid,ct_sha256=digest(('invented_'+sid).encode())),roi_origin='provided_pancreas_reference')
                case|=dict(study_id=sid,protected_role=role,transform=t,transform_sha256=digest(canonical(t)));d=dict(study_id=sid,protected_role=role,operation='optimizer' if role=='train' else 'evaluator',lesion_target_state='verified_negative' if negative else 'positive',geometry=payload['pancreas'][1]['geometry'])
                for kind,(blob,row) in payload.items():
                    uri=sid+'/'+kind+'.nii.gz';entry=row|dict(study_id=sid,protected_role=role,uri=uri,observation=dict(bytes=len(blob)));self.files.append(entry);d[kind]=dict(root_alias='followup_source',uri=uri,bytes=len(blob),content_sha256=row['sha256'])
                case|=dict(descriptor=d,fidelity=dict(metrics={n:dict(native_voxels=v['target_voxels']) for n,v in score['metrics'].items()},outside_pancreas_voxels=score['outside_pancreas_voxels'],source_component_count=len(score['components']),components=[dict(native_voxels=c['native_voxels']) for c in score['components']]),reference_components=[{k:c[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for c in score['components']]);self.cases.append(case)
        order=provider.control['train']+provider.control['validation'];self.cases.sort(key=lambda c:order.index(c['study_id']));self.files=[next(r for r in self.files if r['study_id']==sid and r['kind']==kind) for sid in order for kind in ('pancreas','lesion')]
        self.scope=original_scope(self.cases,self.files,dict(operations=['full_compressed_hash','full_gzip_decode_native_targets'],source_writes=False,global_activation=False),digest(b'invented_no_stat_job'));self.scope['domain']='invented_native_targets';validate_scope(self.scope,provider.control)
    def read(self,session,sid,*,tick=lambda:None):
        require(session.step in STEPS and not session.dirty and (session.step,sid) not in self.used,'Wrong/repeated invented final stage');stage=stage_scope(self.scope,session.step);case=next((c for c in stage['cases'] if c['study_id']==sid),None);require(case is not None,'Absent invented reference');self.used.add((session.step,sid));negative=case['descriptor']['lesion_target_state']=='verified_negative';arrays={};refs=[]
        for row in [r for r in self.files if r['study_id']==sid]:
            blob=self.blobs[negative][row['kind']][0];counts=self.stage_counts[str(session.step)];before_counts=counts.copy()
            try:
                content.hash_exact(io.BytesIO(blob),row,counts,stage['limits'],tick);stored,h,read=content.decode_exact(io.BytesIO(blob),row,counts,stage['limits'],tick)
            finally:
                for key in self.counts:self.counts[key]+=counts[key]-before_counts[key]
            mask,decoding=content.target_content(stored,h,tick);arrays[row['kind']]=mask;refs.append(dict(study_id=sid,protected_role=case['protected_role'],kind=row['kind'],uri=row['uri'],header=h,read=read,decoding=decoding,decoded_sha256=digest(mask.tobytes(order='C'))))
        return arrays['pancreas'],arrays['lesion'],refs
