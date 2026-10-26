#!/usr/bin/env python3
"""Isolated synthetic Prefect selection probe; never a production launcher."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.operations.artifact_store import ArtifactStore
from src.operations.workflow_plan_v1 import encoded,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--version',type=int,default=1)
    parser.add_argument('--fail-middle',action='store_true')
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    # Framework state must be explicitly isolated by the supervisor, before importing Prefect.
    if not os.environ.get('PREFECT_HOME') or os.environ.get('PREFECT_API_URL'):
        raise ValueError('Isolated PREFECT_HOME and no remote API required')
    import prefect
    from prefect import flow,task
    from prefect.cache_policies import NO_CACHE
    artifacts=root/'artifacts';artifacts.mkdir(exist_ok=True)
    refs=root/'references';refs.mkdir(exist_ok=True)
    identity=(root.stat().st_dev,root.stat().st_ino)
    def admit():
        if (root.stat().st_dev,root.stat().st_ino)!=identity:raise OSError('Root replaced')
    store=ArtifactStore(artifacts,check_root=admit,max_bytes=8192,minimum_free_bytes=50_000_000_000)
    code=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    calls=[]
    @task(cache_policy=NO_CACHE,persist_result=False,retries=0,log_prints=False)
    def stage(name,parent=None):
        key=sha(dict(stage=name,parent=parent,version=args.version if name!='source' else 1,code=code))
        artifact='prefect-spike:'+key;reference=refs/(key+'.json')
        payload={'scope':'invented','stage':name,'parent':parent,'version':args.version if name!='source' else 1}
        expected={'value.json':encoded(payload)};checks=0
        def validate(files):
            nonlocal checks
            if files!=expected:raise ValueError('Fixture semantic mismatch')
            checks+=1
            if args.fail_middle and name=='manifest' and checks==2:
                raise RuntimeError('Injected partial publication failure')
            return {'scope':'synthetic','stage':name}
        if reference.exists():
            ref=json.loads(reference.read_bytes())
            store.resolve(artifact,receipt_sha256=ref['receipt_sha256'],expected_derivation=key,validate=validate)
            calls.append({'stage':name,'state':'reused'});return ref
        metadata=dict(artifact_type='synthetic-selection',schema_version='1.0.0',component=name,
            code_sha256=code,parents=[parent] if parent else [],retention='selection-evidence',
            sensitivity='invented',run_id=key,stage_id=name)
        pin,_=store.publish(artifact,derivation_sha256=key,files=expected,metadata=metadata,validate=validate)
        ref={'artifact_id':artifact,'receipt_sha256':pin}
        with reference.open('x') as f:json.dump(ref,f)
        calls.append({'stage':name,'state':'completed'});return ref
    @flow(persist_result=False,retries=0,log_prints=False)
    def fixture():
        a=stage('source');b=stage('manifest',a);return stage('summary',b)
    started=time.monotonic()
    try:
        result=fixture()
    except Exception:
        print(json.dumps({'prefect_version':prefect.__version__,'seconds':time.monotonic()-started,
                          'states':calls,'success':False}),flush=True)
        raise
    print(json.dumps({'prefect_version':prefect.__version__,'seconds':time.monotonic()-started,
                      'states':calls,'success':True,'result':result}),flush=True)


if __name__=='__main__':main()
