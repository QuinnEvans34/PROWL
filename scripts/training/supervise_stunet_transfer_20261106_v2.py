"""Additive correction: canonical pin lookup and failed MLflow init cleanup.

Original supervisor, worker, qualification and failed launch remain untouched.
No retry is dispatched by this module; a new exact-hash receipt is mandatory.
"""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.training import supervise_stunet_transfer_20261106 as original


def input_pin(request):
    canonical=lambda p:os.path.normcase(os.path.abspath(p))
    expected=canonical(request['inputs'])
    matches=[h for p,h in request['pins'].items() if canonical(p)==expected]
    if not matches or len(set(matches))!=1:raise ValueError('Missing/ambiguous input pin')
    if original.sha(request['inputs'])!=matches[0]:raise ValueError('Input pin changed')
    return matches[0]


class Tracking(original.Tracking):
    def __init__(self,request,client=None):
        digest=input_pin(request)  # Validate before creating a tracking record.
        if client is None:
            from mlflow.tracking import MlflowClient
            client=MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
        self.client=client
        exp=client.get_experiment_by_name('PROWL capstone lesion outlining')
        if exp is None:raise ValueError('Existing MLflow experiment missing')
        run=client.create_run(exp.experiment_id,tags={'mlflow.runName':request['title'],'scope':'exploratory_pretrained_provided_pancreas','training_run_id':request['run_id']})
        self.id=run.info.run_id;self.offset=0;self.losses=0
        try:
            for key,value in dict(steps=12000,seed=42,window=128,batch_size=1,precision='fp32',wall_seconds=216000,input_sha256=digest).items():
                client.log_param(self.id,key,value)
        except BaseException:
            client.set_terminated(self.id,status='FAILED');raise


if __name__=='__main__':
    original.Tracking=Tracking
    original.main()
