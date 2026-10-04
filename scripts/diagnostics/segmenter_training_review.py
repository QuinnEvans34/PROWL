"""Read-only independent byte/lineage audit of completed D-326 qualifications."""
from collections import Counter
from pathlib import Path
import json,os,time
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training import segmenter_training_session_v1 as core
from src.operations.localizer_run_storage import tree_bytes
from scripts.diagnostics import segmenter_training_qualification as q,segmenter_checkpoint_inventory as inventory,segmenter_training_policy_parity as parity

DEST=q.ROOT/'SEGMENTER-TRAINING-REVIEW-20261002'
JOB_PINS={
 'SEGMENTER-CHECKPOINT-INVENTORY-20261002':'edef069e1017ba6a7c5d3ff667844f12684b246712cb0c9ec6a35c87a3e30689',
 'SEGMENTER-TRAINING-CPU-20261002':'2d092598abf90603e9166fab03fee8e53aa130528bc2cc9a6a2466fd22376fa6',
 'SEGMENTER-TRAINING-CPU-20261002-RECOVERY':'e85833daeac4d12a7e24d5eb9bfc68011aa0a215722051e93e7423bc8f2e0722',
 'SEGMENTER-TRAINING-MPS-20261002':'cd846e562936c5c7899792e313dffe01320773035a825103a0dccc9576bf9e43',
 'SEGMENTER-TRAINING-MPS-20261002-RECOVERY':'f8a75f15ca60045cac67c69c4b0b5633a36a0dd1075db3729631a8cdb17f9bb6',
 'SEGMENTER-TRAINING-POLICY-PARITY-20261002':'b76d14bb52d5b8fa7fb12a9974b6ad3673badeeaa462925212432a28cff2eb0d',
 'SEGMENTER-TRAINING-CPU-unlaunched01-20261002':'f4e075b3b06aaeadafbb7ccaaac9cab1e860879e6ad2bc3ccea8378aba38c213',
 'SEGMENTER-TRAINING-unlaunched01-SOURCE-20261002':'965cd06c94dc1c4162c335cffbb200fc3a6723b03b7c06a4446c6148d6edac21',
}

def flat(path,pin):
 raw=(path/'receipt.json').read_bytes();require(digest(raw)==pin,'Job receipt changed');receipt=json.loads(raw)
 require(receipt['state']=='complete' and set(receipt['files'])=={p.name for p in path.iterdir() if p.name!='receipt.json'},'Job inventory differs')
 for name,ref in receipt['files'].items():
  p=path/name;require(p.is_file() and not p.is_symlink() and p.name==name,'Unsafe member');b=p.read_bytes();require(ref==dict(bytes=len(b),sha256=digest(b)),'Job bytes differ')
 return receipt

def physical(store,ref,files):
 path=store.root/digest(ref['artifact_id'].encode());raw=(path/'complete.json').read_bytes();require(digest(raw)==ref['receipt_sha256'],'Physical completion pin differs');receipt=json.loads(raw)
 require(receipt['artifact_id']==ref['artifact_id'] and receipt['state']=='complete' and set(p.name for p in path.iterdir())==set(receipt['members'])|{'complete.json','events.jsonl'},'Physical member inventory differs')
 if 'derivation_sha256' in ref:require(receipt['derivation_sha256']==ref['derivation_sha256'],'Physical derivation differs')
 data={}
 for name,expected in receipt['members'].items():
  p=path/name;require(p.is_file() and not p.is_symlink(),'Unsafe physical file');b=p.read_bytes();require(expected==dict(bytes=len(b),sha256=digest(b)),'Physical member differs');data[name]=b
 events=(path/'events.jsonl').read_bytes();require(digest(events)==receipt['events_sha256'],'Physical event pin differs')
 journal=[json.loads(v) for v in events.splitlines()];require(journal[-1]['state']=='validated_ready_to_publish' and all(v['artifact_id']==ref['artifact_id'] and v['sequence']==i for i,v in enumerate(journal)),'Physical event sequence differs')
 files.extend([dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in path.iterdir()]);return data,receipt

def run():
 start=time.monotonic();torch.set_num_threads(2);pins=dict(JOB_PINS);bridge=q.dest('bridge');pins[bridge.name]=digest((bridge/'receipt.json').read_bytes())
 jobs={};job_members=0
 for name,pin in pins.items():
  receipt=flat(q.ROOT/name,pin);job_members+=len(receipt['files'])+1
  if (q.ROOT/name/'result.json').exists():jobs[name]=json.loads((q.ROOT/name/'result.json').read_bytes())
 inv=jobs[inventory.DEST.name];categories=Counter(r['category'] for r in inv['files'])
 require(len(inv['files'])==203 and sum(r['bytes'] for r in inv['files'])==8240982194 and inv['counts']['hash_bytes']==8240982194 and inv['excluded_cache_count']==17021 and inv['model_deserializations']==0,'Historical accounting differs')
 require(sorted(categories.values())==[2,88,113] and all(r['weight_import_allowed'] is False and not r['uri'].startswith('outputs/cache/') for r in inv['files']),'Historical classifications differ')
 frozen=json.loads(q.BUDGET.read_bytes())['ceilings'];stores=q.stores(ceilings=frozen);files=[];artifacts=[];cap=json.loads(q.CAP.read_bytes())
 require(stores[0].root.stat().st_dev!=stores[1].root.stat().st_dev,'Physical domains collide')
 for stage,steps,calls,committed in [('cpu',[0,2,3,6],13,6),('mps',[0,2,3],4,3)]:
  job=jobs[q.dest(stage).name];recovery=jobs[q.dest(stage).name+'-RECOVERY'];request=json.loads((q.dest(stage)/'request.json').read_bytes());identity=request['identity']
  require(job['source_pins']==recovery['source_pins']==q.pins() and request['source_pins']==q.pins(),'Producing source drift')
  require(job['optimizer_calls']==calls and job['committed_steps']==committed and job['dirty_transaction_refused'] and job['real_model_updates']==job['source_arrays_read']==0,'Transaction counts differ')
  require([p['primary']['step'] for p in job['checkpoints']]==steps and [p['step'] for p in recovery['restores']]==steps and recovery['state']=='passed' and recovery['primary_reads_blocked'] and recovery['probability_max_difference']==0 and recovery['next_weight_max_difference']<=1e-6 and recovery['optimizer_calls']==1,'Cold replay differs')
  if stage=='cpu':require(job['cpu_uninterrupted_exact'] and sorted(job['exposure'].values())==[1]*6 and recovery['next_weight_max_difference']==0,'CPU exact epoch/replay differs')
  else:require(recovery['native_replay_exact'],'MPS native replay differs')
  pairs=job['checkpoints']+[job['probes']];restored=[r['reference'] for r in recovery['restores']]+[recovery['probe_restore']]
  for index,(pair,rest) in enumerate(zip(pairs,restored)):
   primary,receipt=physical(stores[0],pair['primary'],files);backup,brec=physical(stores[1],pair['backup'],files);cold,crec=physical(stores[2],rest,files)
   require(backup==cold,'Cold payload/provenance differs from keeper');extras={'primary-complete.json','primary-events.jsonl','catalog.json'};require({n:v for n,v in backup.items() if n not in extras}==primary,'Keeper payload differs')
   primary_path=stores[0].root/digest(pair['primary']['artifact_id'].encode());require(backup['primary-complete.json']==(primary_path/'complete.json').read_bytes() and backup['primary-events.jsonl']==(primary_path/'events.jsonl').read_bytes(),'Keeper primary provenance differs')
   catalog=json.loads(backup['catalog.json']);require(catalog['approval']=='D-326' and catalog['source_reference']==pair['primary'] and catalog['omissions']==[] and catalog['source_domain']==cap['primary_volume_uuid'] and catalog['destination_domain']==cap['backup_volume_uuid'],'Keeper catalog/domain differs')
   require(brec['metadata']['parents']==[pair['primary']['receipt_sha256']] and crec['metadata']['parents']==[pair['backup']['receipt_sha256']],'Keeper/restore parents differ')
   if index<len(steps):
    require(core.validate_payload(primary,identity)==receipt['validation'],'Checkpoint semantics differ')
    require(json.loads(primary['source.json'])==q.pins() and json.loads(primary['initialization.json'])['initial_weights_sha256']==core.INITIAL,'Checkpoint source/init differs')
   else:
    manifest=json.loads(primary['manifest.json']);require(manifest['checkpoints']==job['checkpoints'] and manifest['steps']==steps and len(primary)==7,'Protected probe references differ')
   artifacts.append(dict(stage=stage,primary=pair['primary'],backup=pair['backup'],restore=rest,payload_members=len(primary),payload_bytes=sum(map(len,primary.values()))))
 bridge_result=jobs[bridge.name];rows=bridge_result['cases'];control=bridge_result['control'];require(bridge_result['state']=='qualified_cache_optimizer_boundary_no_updates' and bridge_result['real_updates_denied'] and bridge_result['model_forwards']==bridge_result['model_updates']==bridge_result['source_arrays_read']==0 and bridge_result['source_pins']==q.pins(),'Real bridge scope differs')
 require([r['study_id'] for r in rows]==control['train']+control['validation'] and len(control['train'])==6 and len(control['validation'])==1 and {int(v.rsplit('_',1)[-1]) for v in control['train']}=={3,26,2232,2973,5821,6238} and int(control['validation'][0].rsplit('_',1)[-1])==2514,'Real bridge membership differs')
 for row in rows:require(row['role']==('train' if row['study_id'] in control['train'] else 'validation') and row['target_counts']==control['target_metadata'][row['study_id']]['class_counts'] and row['operation']==('optimizer' if row['role']=='train' else 'evaluator'),'Bridge role/target metadata differs')
 equivalence=jobs[parity.DEST.name];require(equivalence['state']=='passed' and equivalence['probability_max_difference']==0 and equivalence['native_exact'] and equivalence['initial_weights_sha256']==core.INITIAL and equivalence['optimizer_calls']==equivalence['real_inputs']==0,'Baseline policy equivalence differs')
 occupancy=[tree_bytes(s.quota_root) for s in stores];require(all(a<=b for a,b in zip(occupancy,frozen)),'Frozen storage budget exceeded')
 require(not (q.ROOT/'SEGMENTER-TRAINING-CPU-unlaunched01-20261002/consumed.json').exists(),'Retired request consumed')
 DEST.mkdir();source=dict(q.pins());snapshots={}
 for name in q.CODE+[parity.SELF,'scripts/diagnostics/segmenter_training_review.py']:
  raw=(q.REPO/name).read_bytes();n=name.replace('/','__');(DEST/n).open('xb').write(raw);snapshots[name]=dict(file=n,sha256=digest(raw))
 result=dict(state='passed',decision='D-326',source_pins=q.pins(),review_code_sha256=digest(Path(__file__).read_bytes()),job_receipts=pins,job_files_checked=job_members,physical_files_checked=len(files),physical_inventory=files,artifacts=artifacts,source_snapshots=snapshots,historical_categories=dict(categories),historical_bytes=8240982194,storage_ceilings=frozen,storage_occupancy=occupancy,real_bridge_request_sha256=digest((bridge/'request.json').read_bytes()),initial_weights_sha256=core.INITIAL,seconds=time.monotonic()-start)
 q.source.put(DEST/'audit.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('source_pins','physical_inventory','artifacts','source_snapshots','job_receipts')},indent=2))
if __name__=='__main__':run()
