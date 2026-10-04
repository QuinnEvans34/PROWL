from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from src.data.manifest_records import canonical,digest
from src.training import segmenter_v5_training_session_v1 as c,segmenter_training_session_v1 as v3,segmenter_v5_executor_v1 as e,segmenter_v5_comparison_v1 as comparison
from src.operations import segmenter_v5_storage_v1 as storage
from scripts.diagnostics import segmenter_v5_launch as cli
from segmenter_v5_fixtures import request,approval
from test_segmenter_v5_transaction import provider,identity,qualified
from retained_segmenter_metadata import metadata,fixture_path

def test_task_and_numerical_loss_are_separate(identity):
 i,controls=identity;s=c.Session(i,controls)
 assert i['task']!=v3.TASK and i['config']['loss_id']==c.loss_candidate.LOSS
 with pytest.raises(ValueError):v3.validate_payload(c.payload(s),i)
 cfg=v3.config(size=24,steps=6);ctx={n:controls[n] for n in ('source.json','environment.json','geometry.json','lineage.json')};old_i,old_ctrl=v3.make_identity(cfg,provider.__wrapped__(),ctx,run_id='segmenter-training-unit-old',device='cpu')
 with pytest.raises(ValueError):c.validate_payload(v3.payload(v3.Session(old_i,old_ctrl)),i)

def test_update_uses_only_pinned_v5_objective(identity,provider,monkeypatch):
 torch.set_num_threads(2);monkeypatch.setattr(c.numerical,'objective',lambda *a:pytest.fail('v3 numerical objective called'))
 calls=[];fn=c.loss_candidate.objective
 def observed(z,y,loss_id):
  calls.append(loss_id);return fn(z,y,loss_id)
 monkeypatch.setattr(c.loss_candidate,'objective',observed);s=c.Session(*identity);s.update(provider);assert calls==[c.loss_candidate.LOSS]

@pytest.mark.parametrize('loss',[c.numerical.LOSS_V3,'weighted_ce_dice_v4','anything'])
def test_loss_substitution_refused_before_model(identity,loss,monkeypatch):
 i,ctrl=deepcopy(identity);i['config']['loss_id']=loss
 monkeypatch.setattr(c.numerical,'scratch',lambda *a:pytest.fail('Changed loss reached model'))
 with pytest.raises(ValueError):c.Session(i,ctrl)

def cap():return json.loads((Path(__file__).parents[1]/'docs/capstone/operations/SEGMENTER-V5-REHEARSAL-STORAGE-PROPOSAL-2026-10-03.json').read_bytes())['capability']
def storage_approval(c):return canonical(dict(kind='exact_segmenter_v5_storage',decision='D-999-INVENTED',author='Quinton Evans',user_instruction='Invented unit authority only',capability_sha256=digest(canonical(c)),phase=c['phase'],delete_old_evidence=False,real_launch_authorized=False))

def test_storage_proposal_does_not_open_registry(monkeypatch):
 monkeypatch.setattr(storage,'directory',lambda *a:pytest.fail('Unapproved proposal reached roots'))
 raw=canonical(cap())
 with pytest.raises(ValueError):storage.v5_stores('/does-not-exist',raw,trusted_capability_sha256=digest(raw),create=True)

@pytest.mark.parametrize('fault',['scope','phase','kind','author','delete','launch','decision','pin','extra'])
def test_storage_authority_cannot_be_reused_or_expand(fault):
 cp=cap();raw=canonical(cp);a=json.loads(storage_approval(cp))
 if fault=='scope':a['capability_sha256']='0'*64
 elif fault=='phase':a['phase']='real'
 elif fault=='kind':a['kind']='old_short_run_approval'
 elif fault=='author':a['author']='Claude'
 elif fault=='delete':a['delete_old_evidence']=True
 elif fault=='launch':a['real_launch_authorized']=True
 elif fault=='decision':a['decision']='D-333'
 elif fault=='extra':a['unlimited']=True
 approved=canonical(a)
 with pytest.raises(ValueError):storage.validate_storage_authority(raw,approved,'0'*64 if fault=='pin' else digest(approved))

@pytest.mark.parametrize('fault',['ceiling','baseline','max_new','area','registry_extra','real','primary'])
def test_capacity_never_rolls_forward_or_changes_silently(fault):
 cp=cap()
 if fault=='ceiling':cp['absolute_backup_ceiling']+=1
 if fault=='baseline':cp['backup_baseline_bytes']-=1
 if fault=='max_new':cp['max_new_bytes_per_domain']*=2
 if fault=='area':cp['restore_area']='old-consumed-area'
 if fault=='registry_extra':cp['automatic_deletion']=True
 if fault=='real':cp['real_optimizer_updates_allowed']=True
 if fault=='primary':cp['primary_ceiling']*=2
 with pytest.raises(ValueError):storage.validate_capability(canonical(cp))

def test_capacity_authority_is_not_launch_authority():
 r,_=request(real=True);raw=storage_approval(cap())
 with pytest.raises(ValueError):e.authorize(r,raw,trusted_approval_sha256=digest(raw))

def test_dispatch_fails_before_writes_without_storage_approval(tmp_path,monkeypatch):
 r,_=request();monkeypatch.setattr(cli,'checked',lambda *a:r);monkeypatch.setattr(cli,'dest',lambda *a:tmp_path)
 monkeypatch.setattr(cli,'stores',lambda *a,**k:pytest.fail('No storage authority reached stores'))
 with pytest.raises(ValueError):cli.supervise('rehearsal','a'*64)
 assert not list(tmp_path.iterdir())

def test_same_device_backup_is_refused_before_any_payload(identity,tmp_path):
 from types import SimpleNamespace
 from src.operations.segmenter_v5_backup_v1 import backup_checkpoint
 primary=SimpleNamespace(root=tmp_path,resolve=lambda *a,**k:pytest.fail('Not independent'))
 with pytest.raises(ValueError):backup_checkpoint(primary,primary,{},identity[0],source_domain='external',destination_domain='internal')

@pytest.mark.parametrize('field,value',[('primary_step',6),('validation_selects_nothing',False),('lesion_macro_recall_at_least',.1),('volume_bar',835),('promotion_allowed',True)])
def test_comparison_cannot_change_after_freeze(field,value):
 r,_=request(real=True);r['comparison'][field]=value
 with pytest.raises(ValueError):e.validate_request(r)

def historical_rows():
 a=metadata()['before_after'];r=json.loads(fixture_path('CAP-EXP-013-PREPARED-20261003/request.json').read_bytes());rows=[]
 for old,case in zip(a['train']+a['validation'],r['targets']['cases']):
  # Reconstruct integer confusion from retained counts rather than supply arbitrary metrics.
  counts=old['after'];bg=10000000;pan=counts['pancreas_parenchyma'];les=counts['lesion'];fp=les['predicted_voxels']-les['true_positive']-(pan['target_voxels']-pan['true_positive']);matrix=[[bg-fp,0,fp],[pan['target_voxels']-pan['true_positive'],pan['true_positive'],0],[les['target_voxels']-les['true_positive'],0,les['true_positive']]]
  # Preserve the true total lesion prediction by assigning pancreas misses to lesion.
  matrix[1]=[0,0,pan['target_voxels']];matrix[0][2]=les['predicted_voxels']-les['true_positive']-pan['target_voxels'];matrix[0][0]=bg-matrix[0][2]
  rows.append(dict(study_id=old['study_id'],protected_role=old['protected_role'],confusion_matrix=matrix,metrics=c.scoring.from_confusion(matrix),components=old['components_after'],source_affine=np.asarray(case['descriptor']['geometry']['affine_ras']).reshape(4,4).tolist()))
 return rows

def test_comparison_retains_collapse_and_excess_volume_without_promotion():
 result=comparison.assess(historical_rows());assert not result['passed'] and not result['checks']['pancreas_overlap_each'] and result['checks']['all_components_hit'] and not result['promotion_allowed']
 assert max(v['lesion_predicted_reference_ratio'] for v in result['volume_reports'])>835

def test_validation_is_report_only():
 rows=historical_rows();a=comparison.assess(rows);r=rows[-1];m=r['confusion_matrix'];m[0]=[sum(m[0]),0,0];m[1]=[0,sum(m[1]),0];m[2]=[0,0,sum(m[2])];r['metrics']=c.scoring.from_confusion(m)
 for cp in r['components']:cp['true_positive']=cp['native_voxels'];cp['recall']=1.;cp['missed']=False
 b=comparison.assess(rows);assert a['checks']==b['checks'] and a['passed']==b['passed'] and a['aggregates']['validation']!=b['aggregates']['validation']

def test_recovery_store_has_no_primary_path_parameter():
 from inspect import signature
 from src.operations.segmenter_v5_backup_v1 import restore_backup
 assert 'primary' not in signature(restore_backup).parameters

def test_retained_scope_preparation_never_opens_cache_or_arrays(monkeypatch):
 monkeypatch.setattr(cli.q,'BASELINE',fixture_path('accepted-native-baseline.json'))
 monkeypatch.setattr(cli,'ROOT',fixture_path('CAP-EXP-013-PREPARED-20261003/request.json').parents[1])
 monkeypatch.setattr(cli.data,'resolve_qualified',lambda:pytest.fail('Pure scope opened processed arrays'))
 monkeypatch.setattr(cli.oldscore,'inputs',lambda:pytest.fail('Pure scope used old consuming adapter'))
 baseline,scope,cases,files=cli.real_inputs();assert len(cases)==7 and len(files)==14 and scope['limits']==dict(hash_bytes=1265220,decode_bytes=1265220,expanded_bytes=272494704)
 assert [c['study_id'] for c in cases]==comparison.TRAIN+comparison.VALIDATION

def test_consumed_request_refused_before_native_or_storage(tmp_path,monkeypatch):
 r,_=request();(tmp_path/'consumed.json').write_bytes(b'invented consumed marker')
 monkeypatch.setattr(cli,'checked',lambda *a:r);monkeypatch.setattr(cli,'dest',lambda *a:tmp_path);monkeypatch.setattr(cli.parent,'native_preflight',lambda:pytest.fail('Consumed job reached native setup'))
 with pytest.raises(ValueError):cli.supervise('rehearsal','a'*64)

def test_complete_cpu_executor_cadence_and_terminal_primary(tmp_path):
 from test_segmenter_v5_evidence import summary
 from src.operations.artifact_store import ArtifactStore
 torch.set_num_threads(2)
 # The fixture supplies invented native numeric evidence only; this test claims no independent media or native-sized learning.
 (tmp_path/'summary-fixture').mkdir();fake_files,r=summary.__wrapped__(tmp_path/'summary-fixture');_,p=request();job=tmp_path/'job';job.mkdir();root=tmp_path/'store';root.mkdir();st=ArtifactStore(root,check_root=lambda:None,max_bytes=192*1024**2,minimum_free_bytes=0);seen=[]
 def save(s):
  ref=c.publish_checkpoint(st,s);restored=c.resume(st,ref,s.identity);assert c.tree_exact(restored.optimizer.state_dict(),s.optimizer.state_dict());seen.append(s.step)
  return dict(primary=ref,backup=dict(artifact_id='backup:'+ref['artifact_id'],receipt_sha256='b'*64),weights_sha256=c.numerical.state_hash(s.model.state_dict()))
 def finish(s,refs,probs,next_weights,event,check):
  completion=json.loads(fake_files['completion.json']);weights=c.numerical.state_hash(s.model.state_dict());exports=deepcopy(completion['exports'])
  for ex in exports:ex['report']['weights_sha256']=weights
  native={n:fake_files['native-request.json' if n=='request.json' else n] for n in ('request.json','scores.json','references.json','aggregates.json','production.json')}
  from src.training import segmenter_v5_evidence_v1 as ev
  projection=ev.scoring_request(r,[ex['report'] for ex in exports]);native['request.json']=canonical(projection);prod=json.loads(native['production.json']);prod['request_sha256']=digest(canonical(projection));native['production.json']=canonical(prod)
  assert sorted(probs)==[0,2,6] and next_weights['sha256'];return dict(exports=exports,probe_reference=completion['probe_reference'],images_reference=completion['images_reference'],native=native,weights_sha256=weights)
 protected=[]
 def protect(files,i):
  from src.training import segmenter_v5_evidence_v1 as ev
  ev.validate_summary(files,r);protected.append(files);return dict(invented_local_unit_replica_only=True)
 result=e.execute(r,p,job,save_checkpoint=save,finish=finish,protect_summary=protect)
 assert seen==[0,2,6] and result['completed_steps']==6 and sorted(result['exposure'].values())==[1]*6 and len(protected)==1
 assert result['comparison_result'] is None and (job/'transaction.json').exists()

@pytest.mark.parametrize('field,value',[('backup_baseline_bytes',20*1024**3),('absolute_backup_ceiling',22*1024**3)])
def test_budget_stays_inside_registered_twenty_gib(field,value):
 cp=cap();cp[field]=value
 with pytest.raises(ValueError):storage.validate_capability(canonical(cp))

def test_preflight_fault_does_not_consume_or_create_stores(tmp_path,monkeypatch):
 r,_=request();cp=r['storage_capability'];raw=canonical(cp);approved=storage_approval(cp);ca=tmp_path/'cap';ca.write_bytes(raw);ap=tmp_path/'approved';ap.write_bytes(approved)
 monkeypatch.setattr(cli,'checked',lambda *a:r);monkeypatch.setattr(cli,'dest',lambda *a:tmp_path);monkeypatch.setitem(cli.CAPS,'rehearsal',ca);monkeypatch.setitem(cli.STORAGE_APPROVALS,'rehearsal',ap);monkeypatch.setitem(cli.STORAGE_PINS,'rehearsal',digest(approved))
 def failed():raise ValueError('Native memory-monitor preflight unavailable')
 monkeypatch.setattr(cli.parent,'native_preflight',failed);monkeypatch.setattr(cli,'stores',lambda *a,**k:pytest.fail('Failed preflight reached directory creation'))
 with pytest.raises(ValueError):cli.supervise('rehearsal','a'*64)
 assert not (tmp_path/'consumed.json').exists()
