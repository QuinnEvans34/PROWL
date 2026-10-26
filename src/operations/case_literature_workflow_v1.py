"""Bind a pinned offline literature capture to a verified case; never generate an answer."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from .saved_package_workflow_v1 import definition as saved_definition
from .workflow_plan_v1 import Stage,encoded,sha
from .artifact_store import directory,read_file

REPO=Path(__file__).resolve().parents[2]
NODE_VALIDATOR=REPO/'ui/scripts/validateLiteratureCapture.mjs'


def validator_identity():
    paths=[Path(__file__),NODE_VALIDATOR,REPO/'ui/scripts/literatureCaptureContract.js',REPO/'ui/package-lock.json',REPO/'ui/package.json']
    paths+=sorted((REPO/'ui/src').rglob('*.js'))+sorted((REPO/'ui/src').rglob('*.jsx'))
    paths+=sorted((REPO/'configs/evidence').glob('*.json'))
    return sha({str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def validate_capture(raw,*,node):
    # Strict input parsing before handing the same bytes to the production UI validator.
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('Duplicate JSON member')
            result[k]=v
        return result
    json.loads(raw,object_pairs_hook=unique)
    result=subprocess.run([node,str(NODE_VALIDATOR)],input=raw,capture_output=True,timeout=20,cwd=REPO/'ui')
    if result.returncode:
        raise ValueError(result.stderr.decode(errors='replace')[-2000:])
    if len(result.stdout)>16384:raise ValueError('Validator output exceeds budget')
    summary=json.loads(result.stdout)
    if summary.get('validation')!='existing-ui-response-and-citation-contract':
        raise ValueError('Unexpected validation receipt')
    return summary


def definition(source,manifest_pin,capture,capture_pin,*,node=None):
    if not re.fullmatch('[a-f0-9]{64}',capture_pin):raise ValueError('Explicit capture SHA256 required')
    capture=Path(capture).absolute()
    fd=directory(capture.parent)
    try:
        st=os.fstat(fd);source_identity=(st.st_dev,st.st_ino)
    finally:os.close(fd)
    node=node or shutil.which('node')
    if not node:raise ValueError('Node required for existing UI validation')
    node=str(Path(node).resolve(strict=True))
    version=subprocess.run([node,'--version'],capture_output=True,text=True,timeout=5,check=True).stdout.strip()
    if not re.fullmatch(r'v\d+\.\d+\.\d+',version) or int(version.split('.')[0][1:])<24:
        raise ValueError('Node24 or newer required; select the verified UI runtime with --node')
    node_pin=hashlib.sha256(Path(node).read_bytes()).hexdigest()
    policy=validator_identity()
    def captured():
        if validator_identity()!=policy or hashlib.sha256(Path(node).read_bytes()).hexdigest()!=node_pin:
            raise ValueError('Capture validator changed during workflow')
        fd=directory(capture.parent)
        try:
            st=os.fstat(fd)
            if (st.st_dev,st.st_ino)!=source_identity:raise OSError('Capture directory replaced')
            raw=read_file(fd,capture.name,1024**2)
        finally:os.close(fd)
        if hashlib.sha256(raw).hexdigest()!=capture_pin:raise ValueError('Capture pin mismatch')
        return raw
    def literature_files():
        raw=captured();summary=validate_capture(raw,node=node)
        return {'capture.json':raw,'literature-validation.json':encoded(summary)}
    def validate_literature(files):
        if files!=literature_files():raise ValueError('Literature snapshot/validation differs')
        return {'capture_sha256':capture_pin,'validator_sha256':policy}
    stages,handlers,validators=saved_definition(source,manifest_pin)
    stages.append(Stage('literature',inputs={'capture':capture_pin,'validator':policy,'node':node_pin},producer=policy))
    handlers['literature']=lambda p,c:literature_files();validators['literature']=validate_literature
    def linked(handoff,summary):
        return dict(schema='case-literature-handoff-v1',case=handoff,literature=summary,
            capture_sha256=capture_pin,literature_scope='general-literature-associated-for-review-only',
            patient_specific_interpretation=False,measurement_qualification='not_evaluated',
            review_decision=None)
    def assemble(parents,config):
        validators['handoff'](parents['handoff']);validate_literature(parents['literature'])
        handoff=json.loads(parents['handoff']['handoff.json'])
        summary=json.loads(parents['literature']['literature-validation.json'])
        return {**parents['literature'],'linked-handoff.json':encoded(linked(handoff,summary))}
    def validate_linked(files):
        if set(files)!={'capture.json','literature-validation.json','linked-handoff.json'}:
            raise ValueError('Linked handoff inventory differs')
        validate_literature({k:files[k] for k in ('capture.json','literature-validation.json')})
        value=json.loads(files['linked-handoff.json'])
        validators['handoff']({'handoff.json':encoded(value['case'])})
        expected=linked(value['case'],json.loads(files['literature-validation.json']))
        if files['linked-handoff.json']!=encoded(expected):raise ValueError('Linked context differs')
        return {'manifest_sha256':manifest_pin,'capture_sha256':capture_pin,'review_decision':None}
    stages.append(Stage('linked',('handoff','literature'),producer=policy))
    handlers['linked']=assemble;validators['linked']=validate_linked
    return stages,handlers,validators
