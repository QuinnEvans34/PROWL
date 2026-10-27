"""Read-only handoff of frozen cohort and saved on-demand preparation evidence.

No provider construction, scan/cache payload reads, model imports or launch authority.
"""
import hashlib
import json
import os
from pathlib import Path
import re
from src.operations.artifact_store import directory, read_file
from src.operations.workflow_plan_v1 import Stage, encoded, sha
from src.data.manifest_records import canonical, digest
from src.data.segmenter_varied_region_v1 import coverage_slots

KEYS={'control','result','resources','train','development'}


def definition(inputs):
    """inputs maps exact named files to independent path/SHA256 references."""
    if set(inputs)!=KEYS:raise ValueError('Exact prepared input inventory required')
    readers={}
    for key,ref in inputs.items():
        if set(ref)!={'path','sha256'} or not re.fullmatch('[a-f0-9]{64}',ref['sha256']):
            raise ValueError('Explicit input file pin required')
        path=Path(ref['path']).absolute();fd=directory(path.parent)
        try:
            st=os.fstat(fd);identity=(st.st_dev,st.st_ino)
        finally:os.close(fd)
        readers[key]=(path,ref['sha256'],identity)
    def read(key):
        path,pin,identity=readers[key];fd=directory(path.parent)
        try:
            st=os.fstat(fd)
            if (st.st_dev,st.st_ino)!=identity:raise OSError('Input root replaced')
            raw=read_file(fd,path.name,4*1024**2)
        finally:os.close(fd)
        if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('Prepared input pin changed')
        return raw
    def cohort():
        c=json.loads(read('control'));train=read('train').decode().split();dev=read('development').decode().split()
        if (not train or not dev or len(set(train))!=len(train) or len(set(dev))!=len(dev)
            or set(train)&set(dev) or c['train']!=train or c['validation']!=dev):
            raise ValueError('Frozen cohort membership/order differs')
        for key,binding in [('train','train_file'),('development','dev_file')]:
            if hashlib.sha256(read(key)).hexdigest()!=c['bindings'][binding]:raise ValueError('Cohort binding differs')
        if set(c['kd_native_metadata']['pins'])!=set(train):raise ValueError('Native metadata membership differs')
        if any(not re.fullmatch('[a-f0-9]{64}',p) for p in c['kd_native_metadata']['pins'].values()):
            raise ValueError('Native metadata pin invalid')
        if set(c['planned_focused_counts'])!=set(train):raise ValueError('Focused schedule membership differs')
        return c,dict(schema='frozen-cohort-handoff-v1',provider_sha256=digest(canonical(c)),
            train=train,validation=dev,training_authorized=False)
    def prepared():
        c,handoff=cohort();r=json.loads(read('result'));resources=json.loads(read('resources'))
        if (r.get('success') is not True or resources.get('success') is not True or
            resources.get('workers_reaped') is not True or type(resources.get('exit_code')) is not int or resources['exit_code']!=0):
            raise ValueError('Successful reaped preparation required')
        if (r['provider_sha256']!=handoff['provider_sha256'] or r['scientific_ready'] is not False or
            r['ct_voxel_reads']!=0 or r['optimizer_updates']!=0):raise ValueError('Preparation scope/identity differs')
        train=handoff['train'];dev=handoff['validation'];rows=r['rows']
        if [x['case_id'] for x in rows]!=train:raise ValueError('Preparation rows differ from frozen order')
        if r['train']!=len(train) or r['development']!=len(dev):raise ValueError('Preparation cohort counts differ')
        revision=c['label_revision'];corrected=revision['corrected_cases']
        if len(corrected)!=len(set(corrected)) or not set(corrected)<=set(train):raise ValueError('Correction roles differ')
        if c['throughput']!={'version':'errata-kd-on-demand-1','prefetch':False,
            'ct':'original_full_decode_per_visit','labels':'original_with_explicit_errata_overlay'}:
            raise ValueError('Only current on-demand input policy supported')
        for row in rows:
            name=row['case_id'];n=row['focused_visits']
            if n!=c['planned_focused_counts'][name]:raise ValueError('Focused count differs')
            coverage_slots(n,row['coverage_windows'])  # Owning sampling feasibility validator.
            if (type(row['total_visits']) is not int or row['total_visits']<n or
                type(row['positive']) is not bool or row['corrected']!=(name in corrected)):
                raise ValueError('Preparation row qualification differs')
        focused=sum(x['focused_visits'] for x in rows);total=sum(x['total_visits'] for x in rows)
        if (r['focused_updates']!=focused or r['planned_updates']!=total or
            r['context_updates']!=total-focused or r['positive_train']!=sum(x['positive'] for x in rows)):
            raise ValueError('Preparation schedule totals differ')
        return dict(schema='prepared-inputs-handoff-v1',cohort=handoff,
            input_policy=c['throughput'],label_revision=revision,
            native_metadata_count=len(c['kd_native_metadata']['pins']),
            focused_updates=focused,context_updates=total-focused,
            qualification='saved-preparation-metadata-and-cohort-only',
            cache_payloads_revalidated=False,teacher_targets_qualification='not_evaluated',
            scientific_ready=False,training_authorized=False)
    repo=Path(__file__).resolve().parents[2]
    paths=[Path(__file__),repo/'src/operations/workflow_execution_v1.py',repo/'src/operations/workflow_plan_v1.py',
           repo/'src/operations/artifact_store.py',repo/'src/data/segmenter_varied_region_v1.py',repo/'src/data/manifest_records.py']
    producer=sha({str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    def validate_cohort(files):
        if files!={'cohort.json':encoded(cohort()[1])}:raise ValueError('Cohort handoff changed')
        return {'scope':'frozen-membership-only'}
    def validate_prepared(files):
        if files!={'prepared.json':encoded(prepared())}:raise ValueError('Prepared handoff changed')
        return {'scope':'saved-preparation-metadata-only','training_authorized':False}
    def build(parents,config):
        validate_cohort(parents['cohort'])
        return {'prepared.json':encoded(prepared())}
    stages=[Stage('cohort',inputs={k:readers[k][1] for k in ('control','train','development')},producer=producer),
            Stage('prepared',('cohort',),inputs={k:readers[k][1] for k in ('result','resources')},producer=producer)]
    return stages,{'cohort':lambda p,c:{'cohort.json':encoded(cohort()[1])},'prepared':build}, {'cohort':validate_cohort,'prepared':validate_prepared}
