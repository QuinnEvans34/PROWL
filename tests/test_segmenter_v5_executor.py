from copy import deepcopy
import json
import pytest
import torch
from segmenter_v5_fixtures import request,approval
from src.data.manifest_records import canonical,digest
from src.training import segmenter_v5_executor_v1 as e,segmenter_v5_training_session_v1 as core
from src.operations.artifact_store import ArtifactStore
@pytest.fixture
def unit():return request()
@pytest.fixture(scope='module')
def real():return request(real=True)[0]
def test_closed_unit_request(unit):e.validate_request(unit[0])
@pytest.mark.parametrize('fault',['task','head','domain','updates','cadence','evaluation','limits','imports','source','init','continuation','storage','recovery'])
def test_exact_request_refusal(unit,fault):
 r=deepcopy(unit[0])
 if fault=='task':r['task']='localizer'
 if fault=='head':r['identity']['config']['architecture']['out_channels']=2
 if fault=='domain':r['identity']['domain']='qualified_real_cache'
 if fault=='updates':r['identity']['config']['max_steps']=12
 if fault=='cadence':r['checkpoint_steps']=[0,6]
 if fault=='evaluation':r['evaluation_steps']=[0,6]
 if fault=='limits':r['limits']=dict(r['limits'],producer_seconds=9999)
 if fault=='imports':r['weight_imports_allowed']=True
 if fault=='source':r['source_pins']={'forged':'source'}
 if fault=='init':r['initial_weights_sha256']='0'*64
 if fault=='continuation':r['continuation_allowed']=True
 if fault=='storage':r['storage_capability_sha256']='0'*64
 if fault=='recovery':r['recovery_policy']['real_optimizer_calls']=1
 with pytest.raises(ValueError):e.validate_request(r)
def test_real_missing_approval_refused(real):
 with pytest.raises(ValueError):e.authorize(real)
 with pytest.raises(ValueError):e.Grant(object(),'a'*64,'b'*64,'c'*64)
def test_exact_approval_object_and_update_permit(real):
 raw=approval(real);grant=e.authorize(real,raw,trusted_approval_sha256=digest(raw));permit=e.update_permit(real,grant);assert permit.request_sha256==digest(canonical(real))
@pytest.mark.parametrize('fault',['pin','author','kind','decision','request','identity','targets','updates','extension','continuation','extra'])
def test_forged_approval_refused(real,fault):
 a=json.loads(approval(real))
 if fault=='author':a['author']='Claude'
 if fault=='kind':a['kind']='planning_approval'
 if fault=='decision':a['decision']='D-333'
 if fault=='request':a['request_sha256']='0'*64
 if fault=='identity':a['identity_sha256']='0'*64
 if fault=='targets':a['original_final_targets']=False
 if fault=='updates':a['real_updates']=False
 if fault=='extension':a['automatic_extension']=True
 if fault=='continuation':a['continuation']=True
 if fault=='extra':a['override']=True
 raw=canonical(a)
 with pytest.raises(ValueError):e.authorize(real,raw,trusted_approval_sha256='0'*64 if fault=='pin' else digest(raw))
def test_grant_bound_to_request(real):
 raw=approval(real);g=e.authorize(real,raw,trusted_approval_sha256=digest(raw));r=deepcopy(real);r['identity']['run_id']+='-other'
 with pytest.raises(ValueError):e.checked_grant(r,g)
def test_invented_cannot_use_real_authority(unit):
 with pytest.raises(ValueError):e.authorize(unit[0],b'anything',trusted_approval_sha256='a'*64)
def test_journal_chain_detects_edits(tmp_path,unit):
 p=tmp_path/'journal';j=e.Journal(p,unit[0]);j.append(dict(state='attempt_started'));j.append(dict(state='update_complete',completed_step=1));j.append(dict(state='transaction_verified'));j.close();assert len(e.verify_journal(p.read_bytes(),unit[0])[0])==3
 with pytest.raises(ValueError):e.verify_journal(p.read_bytes().replace(b'"completed_step":1',b'"completed_step":2'),unit[0])
@pytest.mark.parametrize('stage',['before_update','after_update','before_evaluation','before_checkpoint','after_checkpoint','before_final','cancel','dirty_optimizer','publish_failure','backup_failure'])
def test_interruption_records_only_last_durable_boundary(tmp_path,unit,stage):
 torch.set_num_threads(2);r,provider=unit;store=ArtifactStore(tmp_path/'store',check_root=lambda:None,max_bytes=192*1024**2,minimum_free_bytes=0);store.root.mkdir();job=tmp_path/'job';job.mkdir();saved=[]
 def save(s):
  if stage=='publish_failure' and s.step==2:raise RuntimeError('publication fault')
  ref=core.publish_checkpoint(store,s)
  if stage=='backup_failure' and s.step==2:raise RuntimeError('keeper fault after primary commit')
  pair=dict(primary=ref,backup=dict(artifact_id='backup:'+ref['artifact_id'],receipt_sha256='b'*64,derivation_sha256=digest(canonical(ref))),weights_sha256=core.numerical.state_hash(s.model.state_dict()));saved.append(pair);return pair
 def fault(where,s):
  if stage=='dirty_optimizer' and where=='before_update' and s.step==2:
   old=s.optimizer.step
   def fail():old();raise RuntimeError('after actual optimizer mutation')
   s.optimizer.step=fail
  if stage=='cancel' and where=='before_update' and s.step==2:raise InterruptedError('cancelled')
  if stage==where and (s.step==2 or where=='before_final'):raise RuntimeError(stage)
 with pytest.raises((RuntimeError,InterruptedError)):
  e.execute(r,provider,job,save_checkpoint=save,finish=lambda *args:pytest.fail('Should not finalize a failed attempt'),protect_summary=lambda *args:pytest.fail('Should not protect failed completion'),fault=fault)
 f=json.loads((job/'transaction-failure.json').read_bytes());assert f['state']=='consumed_incomplete' and f['dirty'] and not (job/'transaction.json').exists();events,_=e.verify_journal((job/'journal.jsonl').read_bytes(),r);durable=[v for v in events if v['state']=='checkpoint_durable'];assert f['last_durable_checkpoint']==(durable[-1]['reference'] if durable else None)
 if stage in ('publish_failure','backup_failure','before_checkpoint','after_checkpoint','before_evaluation'):assert f['last_durable_checkpoint']['primary']['step']==0
 if stage in ('cancel','dirty_optimizer'):assert f['last_durable_checkpoint']['primary']['step']==2
 if stage=='dirty_optimizer':assert f['completed_steps']==2
 with pytest.raises(ValueError):e.execute(r,provider,job,save_checkpoint=save,finish=lambda *a:None,protect_summary=lambda *a:None)
@pytest.mark.parametrize('fault',['validation','tuple','changed_control'])
def test_provider_refused_before_session_or_updates(tmp_path,unit,fault,monkeypatch):
 r,p=unit
 if fault=='tuple':p=(None,None)
 elif fault=='changed_control':p.control['jitter']='changed'
 else:p.control['train'][0]='invented-validation'
 monkeypatch.setattr(core,'Session',lambda *a:pytest.fail('Invalid provider reached model'))
 with pytest.raises(ValueError):e.execute(r,p,tmp_path,save_checkpoint=lambda s:None,finish=lambda *a:None,protect_summary=lambda *a:None)
@pytest.mark.parametrize('fault',['missing','kind','producer','test_record'])
def test_real_readiness_required_before_authority(real,fault):
 r=deepcopy(real)
 if fault=='missing':r['readiness']={}
 if fault=='kind':r['readiness']['kind']='D326_only'
 if fault=='producer':r['readiness']['producer_receipt_sha256']='short'
 if fault=='test_record':r['readiness']['tests_sha256']=None
 with pytest.raises(ValueError):e.validate_request(r)

def test_mps_fallback_setting_cannot_be_misreported(monkeypatch):
 from scripts.diagnostics import segmenter_short_launch as cli
 monkeypatch.setenv('PYTORCH_ENABLE_MPS_FALLBACK','1')
 with pytest.raises(ValueError):cli.runtime()

def test_source_drift_stops_at_boundary_with_previous_keeper(tmp_path,unit):
 torch.set_num_threads(2);r,p=unit;counter=0;st=ArtifactStore(tmp_path/'store',check_root=lambda:None,max_bytes=192*1024**2,minimum_free_bytes=0);st.root.mkdir();job=tmp_path/'job';job.mkdir()
 def verify():
  nonlocal counter
  counter+=1
  if counter==3:raise ValueError('source drift at step2')
 def save(s):
  ref=core.publish_checkpoint(st,s);return dict(primary=ref,backup=dict(artifact_id='backup:'+ref['artifact_id'],receipt_sha256='b'*64),weights_sha256=core.numerical.state_hash(s.model.state_dict()))
 with pytest.raises(ValueError):e.execute(r,p,job,save_checkpoint=save,finish=lambda *a:pytest.fail('Drift reached final stage'),protect_summary=lambda *a:None,verify_source=verify)
 f=json.loads((job/'transaction-failure.json').read_bytes());assert f['completed_steps']==2 and f['last_durable_checkpoint']['primary']['step']==0

