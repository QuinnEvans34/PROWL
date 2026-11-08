"""Pre-dispatch supervisor-runtime admission; preserve failed a01 and frozen worker."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.training import supervise_stunet_continuation_20261108 as original
_verify=original.verify
_Tracking=original.Tracking


def verify_recovery(request,mode):
    if mode!='science':raise ValueError('One corrected scientific launch only')
    if request.get('failed_attempt_charge_seconds')!=60 or request['seconds']!=144000-60:
        raise ValueError('Original 40h total includes conservative failed-attempt charge')
    failure=json.loads(Path(request['failed_attempt_resources']).read_text())
    if failure.get('success') is not False or not failure.get('workers_reaped') or failure.get('seconds',999)>60:
        raise ValueError('Unaccounted or live failed attempt')
    _verify(dict(request,seconds=144000),mode)


class Tracking(_Tracking):
    def __init__(self,request,client=None):
        super().__init__(request,client=client)
        try:
            self.client.log_param(self.id,'remaining_wall_seconds',request['seconds'])
            self.client.log_param(self.id,'failed_attempt_charge_seconds',request['failed_attempt_charge_seconds'])
        except BaseException:
            self.client.set_terminated(self.id,status='FAILED');raise


def validate_supervisor(request,executable,client=None):
    canonical=lambda x:os.path.normcase(os.path.abspath(x))
    expected=str(ROOT/'.venv-prowl-windows/Scripts/python.exe')
    if canonical(request['supervisor_python'])!=canonical(expected) or canonical(executable)!=canonical(expected):
        raise ValueError('Use the frozen MLflow supervisor environment')
    if client is None:
        from mlflow.tracking import MlflowClient
        client=MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
    experiment=client.get_experiment_by_name('PROWL capstone lesion outlining')
    if experiment is None:raise ValueError('Existing MLflow experiment missing')
    return dict(supervisor_python=expected,experiment_id=experiment.experiment_id,tracking_import_and_read=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);p.add_argument('--mode',required=True,choices=['science']);p.add_argument('--preflight-only',action='store_true');a=p.parse_args()
    if original.sha(a.request)!=a.sha256:raise ValueError('Request hash mismatch')
    request=json.loads(Path(a.request).read_text())
    # Admission must complete before any artifact, training worker or MLflow run exists.
    runtime=validate_supervisor(request,sys.executable)
    if request.get('corrected_attempt_authorized') is not True:
        raise ValueError('Explicit approval required for one corrected scientific attempt')
    verify_recovery(request,a.mode)
    original.input_pin(request)
    import psutil
    import mlflow
    original.require_ac();original.check_storage()
    if a.preflight_only:
        print(json.dumps(dict(status='PASS_SUPERVISOR_PREFLIGHT_ONLY',runtime=runtime,mlflow_version=mlflow.__version__,psutil_version=psutil.__version__,worker_python=request['python'],worker_script=str(ROOT/'scripts/training/train_stunet_continuation_20261108.py'),scientific_updates=0,mlflow_run_created=False)),flush=True)
        return
    original.verify=verify_recovery;original.Tracking=Tracking
    original.main()


if __name__=='__main__':main()
