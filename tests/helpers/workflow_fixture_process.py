"""Subprocess fault injection, exclusively invented inputs and bounded CPU waits."""
import os
from pathlib import Path
import sys
import time

from src.operations.case_evidence_workflow_v1 import definition
from src.operations.workflow_execution_v1 import Executor

root=Path(sys.argv[1]);identity=sys.argv[2];mode=sys.argv[3]
e=Executor(root,check_root=lambda:None,minimum_free_bytes=0)
s,h,v=definition()
original=v['evidence'];calls=0

def interrupted(files):
    global calls
    result=original(files);calls+=1
    if calls==2:  # Persisted members exist in the publisher's hidden attempt.
        (root/'publication-ready').write_text('synthetic evidence staged')
        if mode=='hold':time.sleep(30)
        elif mode=='fail':raise RuntimeError('injected persisted-output failure')
    return result

v['evidence']=interrupted
if mode=='orphan':
    original_store=e.store
    def store():
        store=original_store();publish=store.publish
        def patched(*args,**kwargs):
            result=publish(*args,**kwargs)
            if kwargs['metadata']['stage_id']=='evidence':os._exit(99)
            return result
        store.publish=patched;return store
    e.store=store
try:e.execute(s,h,v,identity=identity)
except Exception:sys.exit(1)
