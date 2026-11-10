"""Register selected STU-Net neural network only; CPU serialization and exact reload."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['MLFLOW_DISABLE_AGENT_HINT']='1'
import sys,json,hashlib,gc
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import torch,cloudpickle,mlflow,mlflow.pytorch
from mlflow.tracking import MlflowClient
from src.training.stunet_transfer_20261106 import make_model,sha256

def main():
 torch.set_num_threads(1)
 run='13c709ae157949988de1d7f8821a03b7'
 folder=Path('E:/PROWL/artifacts/pants_stunet_corrected_continuation_12k_20261108_launch02/execution')
 selected=json.loads((folder/'selected.json').read_text());cp=selected['checkpoint']
 assert selected['step']==18000
 assert sha256(cp['path'])==sha256(cp['backup'])==cp['sha256']
 root=Path('E:/PROWL/readiness/stunet-selected-registration-20261109-a01');root.mkdir(exist_ok=False)
 model=make_model('E:/PROWL/teachers/stunet-base-0652eaf5-20261106/STUNetTrainer.py',pools=[[2,2,2]]*4+[[1,1,2]])
 state=torch.load(cp['path'],map_location='cpu',weights_only=True)
 assert state['step']==18000 and state['identity']['nonpromotable'] is False
 model.load_state_dict(state['model'],strict=True);model.eval();model.decoder.deep_supervision=False
 del state;gc.collect()
 meta={'component':'neural-network-only','checkpoint_sha256':cp['sha256'],'checkpoint_step':18000,'development_lesion_dice':selected['lesion_dice'],'scope':'provided_pancreas_region_exploratory','pretraining_overlap':'unresolved','fixed_5mm_filter_applied':False,'parent_training_run':run,'serving_promotion':False,'serialization_runtime':torch.__version__,'preprocessing':'Use frozen STU-Net physical input/reconstruction pipeline; this package takes normalized 3D tensors, not CT files.'}
 package=root/'model'
 mlflow.pytorch.save_model(model,str(package),pickle_module=cloudpickle,serialization_format='pickle',pip_requirements=['torch=='+torch.__version__,'cloudpickle=='+cloudpickle.__version__],metadata=meta)
 restored=mlflow.pytorch.load_model(str(package),map_location='cpu')
 a=model.state_dict();b=restored.state_dict();assert a.keys()==b.keys() and all(torch.equal(a[k],b[k]) for k in a)
 assert restored.decoder.deep_supervision is False and not restored.training and not torch.cuda.is_initialized()
 del restored,model;gc.collect()
 (root/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
 mlflow.set_tracking_uri('sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db');client=MlflowClient()
 assert client.get_run(run).info.status=='FINISHED'
 name='prowl-stunet-pancreas-assisted-research'
 existing=list(client.search_registered_models(filter_string="name = '"+name+"'"))
 if not existing:client.create_registered_model(name,description='Exploratory STU-Net neural network; supplied-pancreas development selection, unresolved pretraining overlap. Not a deployed diagnostic model.')
 versions=list(client.search_model_versions(filter_string="name = '"+name+"'"))
 assert not any(v.tags.get('checkpoint_sha256')==cp['sha256'] for v in versions),'Already registered'
 artifact='registered-selected-stunet-18000-20261109'
 client.log_artifacts(run,str(package),artifact_path=artifact)
 client.log_artifact(run,str(root/'provenance.json'),artifact_path=artifact)
 v=client.create_model_version(name,source='runs:/'+run+'/'+artifact,run_id=run,tags={'checkpoint_sha256':cp['sha256'],'checkpoint_step':'18000','development_lesion_dice':str(selected['lesion_dice']),'scope':'provided_pancreas_region_exploratory','deployment_approved':'false'},description='Selected best raw development Dice .4305169672 at global18000. Exact CPU save/reload tensors verified; preprocessing and native reconstruction remain separate.')
 got=client.get_model_version(name,v.version);assert got.run_id==run and got.tags['checkpoint_sha256']==cp['sha256'];assert client.get_run(run).info.status=='FINISHED'
 receipt=dict(status='PASS',registry_name=name,version=v.version,source=got.source,run_id=run,checkpoint_sha256=cp['sha256'],step=18000,dice=selected['lesion_dice'],exact_CPU_reload=True,new_training_seconds=0,model_files={str(f.relative_to(package)):sha256(f) for f in package.rglob('*') if f.is_file()})
 (root/'registration.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
