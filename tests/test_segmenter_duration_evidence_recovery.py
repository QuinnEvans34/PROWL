from copy import deepcopy
import json
import pytest
from segmenter_duration_fixtures import request,FakeSession,checkpoint,screen_pair
from src.data.manifest_records import canonical,digest
from src.training import segmenter_duration_executor_v1 as e,segmenter_duration_evidence_v1 as evidence
from src.operations import segmenter_duration_backup_v1 as backup
from src.operations.artifact_store import ArtifactStore

@pytest.fixture
def complete(tmp_path):
    r,p=request();screens=[];captured={}
    def screen(s,ref,tick):
        record,pair=screen_pair(r,s,50);screens.append(record);return record,pair
    def protect(files,identity):captured.update(files);return {'invented_keeper':True}
    result=e.execute(r,p,tmp_path,save_checkpoint=checkpoint,screen=screen,protect_summary=protect,finish=lambda *a:dict(screen_records=screens,exports=[],images_reference=None,probe_reference=None,next_state_reference=None),session_factory=FakeSession)
    return r,captured,result

def test_summary_binds_journal_and_equal_exposures(complete):
    r,files,result=complete;valid=evidence.validate_summary(files,r)
    assert result['state']=='complete' and result['terminal_decision']=='terminal_pass' and set(result['exposure'].values())=={1}
    assert valid['completed_steps']==6 and result['recovery']['model_calls']==dict(forwards=0,optimizer_calls=0)

@pytest.mark.parametrize('fault',['checkpoint','last_keeper','screen','exposure','terminal','task','journal','extra','calls','recovery'])
def test_completion_and_proof_forgery_refused(complete,fault):
    r,files,result=complete;files=deepcopy(files);v=json.loads(files['completion.json'])
    if fault=='checkpoint':v['checkpoints'].pop(1)
    if fault=='last_keeper':v['last_durable_checkpoint']=v['checkpoints'][0]
    if fault=='screen':v['screens'][0]['screen_sha256']='0'*64
    if fault=='exposure':next(iter(v['exposure']));v['exposure'][next(iter(v['exposure']))]=2
    if fault=='terminal':v['completed_steps']=5
    if fault=='task':v['task']='prior_v5_summary'
    if fault=='journal':files['journal.jsonl']=files['journal.jsonl'].replace(b'update_complete',b'update_unknown',1)
    if fault=='extra':v['promoted']=True
    if fault=='calls':v['recovery']['model_calls']['forwards']=True
    if fault=='recovery':v['recovery']['screen_records']=[]
    files['completion.json']=canonical(v)
    with pytest.raises((ValueError,KeyError)):evidence.validate_summary(files,r)


def backup_fixture():
    payload={'invented.txt':b'not images or model weights'};identity={'run_id':'invented','source_sha256':'a'*64};reference=dict(artifact_id='invented:screen',receipt_sha256=None,derivation_sha256='b'*64)
    valid=lambda f,i:dict(invented_sha256=digest(f['invented.txt']))
    events=b'invented event';receipt=dict(state='complete',artifact_id=reference['artifact_id'],derivation_sha256=reference['derivation_sha256'],metadata=dict(artifact_type='segmenter-duration-native-screen'),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in payload.items()},events_sha256=digest(events),validation=valid(payload,identity))
    raw=canonical(receipt);reference['receipt_sha256']=digest(raw)
    catalog=dict(source_reference=reference,source_domain='invented-A',destination_domain='invented-B',approval='DUR-02',omissions=[],state='verified_snapshot')
    files=payload|{'primary-complete.json':raw,'primary-events.jsonl':events,'catalog.json':canonical(catalog)}
    return files,reference,identity,valid

@pytest.mark.parametrize('fault',[None,'payload','receipt','events','catalog','semantic'])
def test_backup_verifies_payload_receipt_journal_and_semantics(fault):
    files,ref,i,validator=backup_fixture()
    if fault=='payload':files['invented.txt']+=b'changed'
    if fault=='receipt':ref['receipt_sha256']='0'*64
    if fault=='events':files['primary-events.jsonl']+=b'changed'
    if fault=='catalog':v=json.loads(files['catalog.json']);v['omissions']=['file'];files['catalog.json']=canonical(v)
    if fault=='semantic':validator=lambda *a:{'forged':True}
    if fault is None:assert backup.validate_backup(files,i,ref,validator)['primary_receipt_sha256']==ref['receipt_sha256']
    else:
        with pytest.raises(ValueError):backup.validate_backup(files,i,ref,validator)


def test_cold_restore_uses_only_keeper_and_fresh_destination(tmp_path):
    files,ref,i,validator=backup_fixture();keeper=ArtifactStore(tmp_path/'keeper',check_root=lambda:None,max_bytes=4096,minimum_free_bytes=0);keeper.root.mkdir();restore=ArtifactStore(tmp_path/'restore',check_root=lambda:None,max_bytes=4096,minimum_free_bytes=0);restore.root.mkdir()
    aid='backup:'+ref['artifact_id'];derivation=digest(canonical(ref));validate=lambda f:backup.validate_backup(f,i,ref,validator)
    metadata=dict(artifact_type='segmenter-backup',schema_version='1.0.0',component='invented',code_sha256='a'*64,parents=[],retention='required',sensitivity='invented',run_id='invented',stage_id='backup')
    pin,_=keeper.publish(aid,derivation_sha256=derivation,files=files,metadata=metadata,validate=validate)
    recovered,new=backup.restore_backup(keeper,restore,dict(artifact_id=aid,receipt_sha256=pin,derivation_sha256=derivation),ref,i,validator)
    assert recovered=={'invented.txt':b'not images or model weights'} and new['artifact_id'].startswith('restore:')
    _,second=backup.restore_backup(keeper,restore,dict(artifact_id=aid,receipt_sha256=pin,derivation_sha256=derivation),ref,i,validator)
    assert new['artifact_id']!=second['artifact_id']


def test_same_device_cannot_be_independent_keeper(tmp_path):
    a=ArtifactStore(tmp_path/'a',check_root=lambda:None,max_bytes=4096,minimum_free_bytes=0);a.root.mkdir();b=ArtifactStore(tmp_path/'b',check_root=lambda:None,max_bytes=4096,minimum_free_bytes=0);b.root.mkdir()
    with pytest.raises(ValueError,match='Independent'):backup.backup_checkpoint(a,b,{}, {},source_domain='one',destination_domain='two')


def test_prior_acceptance_metadata_never_reopens_model_payload(tmp_path,monkeypatch):
    from scripts.diagnostics import segmenter_duration_launch as cli
    numeric=canonical(dict(state='invented_prior_qualified',original_arrays=0));(tmp_path/'result.json').write_bytes(numeric)
    receipt=canonical(dict(state='complete',files={'result.json':dict(bytes=len(numeric),sha256=digest(numeric)),'weights.pt':dict(bytes=99,sha256='f'*64)}));(tmp_path/'receipt.json').write_bytes(receipt)
    assert cli.metadata_result(tmp_path,digest(receipt))==json.loads(numeric)
    assert not (tmp_path/'weights.pt').exists()


@pytest.fixture(scope='module')
def tiny_native_stages():
    """Seven independent 8³ invented references; no source/cache/model arrays."""
    from io import BytesIO
    import numpy as np
    from src.data import segmenter_duration_targets_v1 as targets,segmenter_content_v1 as content
    from src.training import segmenter_native_scoring_v1 as scoring
    cases=[];rows=[];references=[];scores=[];exports=[]
    for index in range(7):
        sid='invented-native-'+str(index);role='train' if index<6 else 'validation'
        pan=np.zeros((8,8,8),np.uint8);pan[1:7,1:7,1:7]=1;les=np.zeros_like(pan)
        if index!=4:les[2:4,2:4,2:4]=1
        if index==1:les[0,2,2]=1
        prediction=np.where(les,2,pan).astype(np.uint8)
        descriptor=dict(study_id=sid,protected_role=role);local=[]
        for kind,array in [('pancreas',pan),('lesion',les)]:
            blob,row=targets.invented_blob(array,kind);uri=sid+'/'+kind+'.nii.gz'
            row|=dict(study_id=sid,protected_role=role,uri=uri,observation=dict(bytes=len(blob)))
            counts={k:0 for k in ('hash_bytes','decode_bytes','expanded_bytes')}
            limits=dict(hash_bytes=len(blob),decode_bytes=len(blob),expanded_bytes=row['expanded_bytes'])
            content.hash_exact(BytesIO(blob),row,counts,limits,lambda:None)
            stored,header,read=content.decode_exact(BytesIO(blob),row,counts,limits,lambda:None)
            decoded,decoding=content.target_content(stored,header)
            assert np.array_equal(decoded,array) and counts==limits
            references.append(dict(study_id=sid,protected_role=role,kind=kind,uri=uri,header=header,read=read,decoding=decoding,decoded_sha256=digest(decoded.tobytes(order='C'))))
            descriptor[kind]=dict(root_alias='followup_source',uri=uri,bytes=len(blob),content_sha256=row['sha256'])
            rows.append(row);local.append(row)
        descriptor['geometry']=local[0]['geometry']
        scored=scoring.score(prediction,pan,les,target_state='verified_negative' if index==4 else 'positive')
        native_sha=digest(prediction.tobytes(order='C'))
        truth=np.where(les,2,pan)
        # Independent cell-count oracle, separate from the scorer's binned code path.
        oracle=[[int(np.count_nonzero((truth==a)&(prediction==b))) for b in range(3)] for a in range(3)]
        assert oracle==scored['confusion_matrix']
        scores.append(scored|dict(study_id=sid,protected_role=role,source_shape=[8,8,8],source_affine=np.asarray(descriptor['geometry']['affine_ras']).reshape(4,4).tolist(),prediction_sha256=native_sha,oracle=dict(state='passed',confusion_matrix=oracle)))
        exports.append(dict(native_sha256=native_sha,class_counts=[int(np.count_nonzero(prediction==n)) for n in range(3)]))
        cases.append(dict(study_id=sid,protected_role=role,descriptor=descriptor,fidelity=dict(metrics={n:dict(native_voxels=v['target_voxels']) for n,v in scored['metrics'].items()},outside_pancreas_voxels=scored['outside_pancreas_voxels'],source_component_count=len(scored['components']),components=[dict(native_voxels=c['native_voxels']) for c in scored['components']]),reference_components=[{k:c[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for c in scored['components']]))
    scope=targets.original_scope(cases,rows,dict(operations=['full_compressed_hash','full_gzip_decode_native_targets'],source_writes=False,global_activation=False),digest(b'invented-only-metadata'));scope['domain']='invented_native_targets'
    r=dict(targets=scope,source_pins={'invented-stage-code':'a'*64},runtime=dict(domain='invented-stage-unit'))
    def at(step):
        length=7 if step==192 else 6;stage_exports=deepcopy(exports[:length])
        projection=evidence.scoring_request(r,stage_exports,step);pin=digest(canonical(projection))
        files={'request.json':canonical(projection),'scores.json':canonical(scores[:length]),'references.json':canonical(references[:2*length]),'aggregates.json':canonical(scoring.aggregates(scores[:length])),'production.json':canonical(dict(request_sha256=pin,source_counts=projection['limits'],source_arrays_read=2*length,ct_arrays_read=0,model_forwards=0,model_updates=0,code_pins=r['source_pins'],runtime=r['runtime'],mount_before=dict(domain='invented-only'),mount_after=dict(domain='invented-only')))}
        return deepcopy(r),files,stage_exports
    return at


@pytest.mark.parametrize('step',[48,96,144,192])
def test_native_duration_stage_validates_full_reference_evidence(tiny_native_stages,step):
    r,files,exports=tiny_native_stages(step)
    valid=evidence.validate_native(files,r,exports,step)
    assert (valid['cases'],valid['references'])==((7,14) if step==192 else (6,12))
    assert valid['source_counts']==r['targets']['stage_limits'][str(step)]
    aggregates=json.loads(files['aggregates.json'])
    assert aggregates['train']['cases']==6 and ('validation' in aggregates)==(step==192)
    from src.training import segmenter_native_scoring_v1 as scoring
    identity=dict(request=json.loads(files['request.json']),request_sha256=digest(files['request.json']))
    if step==192:assert scoring.validate_payload(files,identity)['cases']==7
    else:
        with pytest.raises(ValueError,match='case/reference inventory'):scoring.validate_payload(files,identity)


@pytest.mark.parametrize('fault',['case','reference','export','role','component','oracle','geometry','compressed_hash','header_hash','decoding','source_arrays','source_bytes','aggregate','reference_bounds'])
def test_native_duration_stage_retains_closed_evidence_guards(tiny_native_stages,fault):
    r,files,exports=tiny_native_stages(48)
    if fault in ('case','component','oracle','geometry'):
        value=json.loads(files['scores.json'])
        if fault=='case':value.pop()
        if fault=='component':value[0]['components'][0]['true_positive']-=1
        if fault=='oracle':value[0]['oracle']['confusion_matrix'][0][0]+=1
        if fault=='geometry':value[0]['source_shape']=[9,8,8]
        files['scores.json']=canonical(value)
    elif fault in ('reference','compressed_hash','header_hash','decoding'):
        value=json.loads(files['references.json'])
        if fault=='reference':value.pop()
        if fault=='compressed_hash':value[0]['read']['sha256']='f'*64
        if fault=='header_hash':value[1]['header']['header_sha256']='f'*64
        if fault=='decoding':value[0]['decoding']['max_endpoint_residual']=.01
        files['references.json']=canonical(value)
    elif fault in ('source_arrays','source_bytes'):
        value=json.loads(files['production.json'])
        if fault=='source_arrays':value['source_arrays_read']=14
        else:value['source_counts']['hash_bytes']+=1
        files['production.json']=canonical(value)
    elif fault=='aggregate':files['aggregates.json']=canonical({})
    else:
        if fault=='export':exports.pop()
        if fault=='role':r['targets']['cases'][0]['protected_role']='validation'
        if fault=='reference_bounds':r['targets']['cases'][0]['reference_components'][0]['bounds_xyz_half_open']=[[1,3]]*3
        files['request.json']=canonical(evidence.scoring_request(r,exports,48))
        production=json.loads(files['production.json']);production['request_sha256']=digest(files['request.json']);files['production.json']=canonical(production)
    with pytest.raises(ValueError):evidence.validate_native(files,r,exports,48)
