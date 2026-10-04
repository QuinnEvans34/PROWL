"""Fresh per-evaluation native-reference scopes for the exact CAP-EXP-007 identity.

No D-304 request replay. Scope is derived from the approved plan and qualified cache
binding, then independently resolved against the original frozen cohort.
"""
from copy import deepcopy
from pathlib import Path
import os
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data.native_localizer_references import ReadBudget,NativeReferences,resolve_qualified_scope
from src.data.twomm_cache_inputs import REGISTRY
from src.training.twomm_training import validate_controls

SOURCE_ROOT='/Volumes/PROWL-Data/PROWL/sources/pants/extraction-3b1cd6110811-20260922'
VOLUME='22750B93-2F3F-499D-87F5-902981BFAB59'


def rebound_observation(row,device):
    """Only the ephemeral mount device may differ; original inventory is never rewritten."""
    require(type(device) is int and device>0 and
        set(row['observation'])=={'device','inode','mtime_ns','ctime_ns'},'Invalid mount observation')
    result=deepcopy(row);result['observation']['device']=device;return result


class VolumeReboundReferences(NativeReferences):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._device=self._root.stat().st_dev
    def _read(self,row,cap):
        from src.data.bounded_nifti_audit import read_file
        from src.data.native_localizer_references import LIMITS
        self._check();require(self._root.stat().st_dev==self._device,'Source mount changed')
        image,receipt=read_file(self._root,rebound_observation(row,self._device),
            compressed_cap=LIMITS['per_file_compressed'],expanded_cap=cap,voxel_cap=LIMITS['voxels'],tick=self._check)
        receipt['filesystem_observation']=dict(policy='verified_volume_device_rebound_v1',
            verified_volume_uuid=VOLUME,retained_device=row['observation']['device'],live_device=self._device)
        return image,receipt


def qualified_items(repo,binding,*,tick=lambda:None):
    cap=dict(registry_sha256=REGISTRY,source_root=SOURCE_ROOT,volume_uuid=VOLUME,
        members={r:[e['descriptor']['study_id'] for e in es] for r,es in binding['roles'].items()})
    items,root,check=resolve_qualified_scope(Path(repo),cap,tick=tick)
    require(items=={r:[e['descriptor'] for e in es] for r,es in binding['roles'].items()},'Reference/cohort qualification differs')
    return items,root,check


def mount_observation(repo,binding):
    """UUID-verified metadata-only receipt, frozen with the replacement request."""
    from src.data.bounded_nifti_audit import open_relative,signature
    items,root,check=qualified_items(repo,binding);device=root.stat().st_dev;rows=[]
    for role,ds in items.items():
        for d in ds:
            check();row=d['rows']['pancreas'];fd=open_relative(root,row['uri'])
            try:live=signature(os.fstat(fd))
            finally:os.close(fd)
            retained=dict(row['observation'],bytes=row['bytes'])
            require(live==dict(retained,device=device),'Non-device source identity changed')
            rows.append(dict(role=role,study_id=d['study_id'],uri=row['uri'],retained=retained,live=live))
    check();return dict(schema_version='twomm-source-mount-observation-1',policy='verified_volume_device_rebound_v1',
        volume_uuid=VOLUME,source_root=str(root),live_device=device,source_bytes_read=0,rows=rows)


def scope(binding,plan):
    stages=[]
    for e in plan['evaluations']:
        rows=[entry['descriptor']['rows']['pancreas'] for role in e['roles'] for entry in binding['roles'][role]]
        stages.append(dict(step=e['step'],roles=e['roles'],files=len(rows),
            compressed_bytes=sum(r['bytes'] for r in rows),expanded_bytes=sum(r['expanded_bytes'] for r in rows)))
    return dict(schema_version='twomm-training-reference-scope-1',stages=stages,
        files=sum(s['files'] for s in stages),compressed_bytes=sum(s['compressed_bytes'] for s in stages),
        expanded_bytes=sum(s['expanded_bytes'] for s in stages),ct_files=0)


class StagedReferences:
    def __init__(self,items,root,check,plan,*,reader=NativeReferences):
        self._items=deepcopy(items);self._root=root;self._check=check;self._plan=deepcopy(plan)
        self._pin=digest(canonical(dict(items=items,plan=plan)));self.budgets=[];self.next_stage=0;self._reader=reader
    def open(self,stage,guard):
        require(digest(canonical(dict(items=self._items,plan=self._plan)))==self._pin,'Reference scope changed')
        require(self.next_stage<len(self._plan['evaluations']) and stage==self._plan['evaluations'][self.next_stage],
            'Unscoped/repeated/out-of-order reference stage')
        if self.budgets:self._complete(self.budgets[-1])
        # Claim before exposing the reader: interruption never silently reopens the stage.
        self.next_stage+=1
        items=[d for role in stage['roles'] for d in self._items[role]];budget=ReadBudget(items);self.budgets.append(budget)
        def check():guard();self._check()
        check();return {role:self._reader(self._items[role],self._root,check,budget,role) for role in stage['roles']}
    @staticmethod
    def _complete(budget):
        require(budget.pending is None and budget.files==len(budget.expected) and
            budget.compressed==budget.compressed_cap and budget.expanded==budget.expanded_cap,'Incomplete prior reference stage')
    def completed(self,*,through_step=None):
        expected=self._plan['evaluations']
        if through_step is not None:
            require(self._plan['schema_version'] in ('twomm-training-plan-2','twomm-training-plan-3') and
                through_step in self._plan['checkpoint_steps'],'Invalid stopped reference boundary')
            expected=[s for s in expected if s['step']<=through_step]
        require(self.next_stage==len(expected),'Incomplete reference cadence')
        for b in self.budgets:self._complete(b)
        return dict(files=sum(b.files for b in self.budgets),compressed_bytes=sum(b.compressed for b in self.budgets),
            expanded_bytes=sum(b.expanded for b in self.budgets),ct_files=0)


def open_training_references(repo,identity,controls,*,tick=lambda:None):
    binding,plan=validate_controls(identity,controls)
    require(identity['purpose']=='qualified-twomm-training','Real reference reader requires real launch identity')
    expected=scope(binding,plan)
    extended=identity['schema_version'] in ('twomm-training-2','twomm-training-3')
    # Exact stage scope is derived from the same independently qualified descriptor bytes.
    if identity['schema_version']=='twomm-training-2':
        require(expected['files']==426 and expected['compressed_bytes']==58_621_113 and
            expected['expanded_bytes']==11_763_565_147,'Exact extended stage read budget differs')
    else:
        require(expected['files']==386 and expected['compressed_bytes']==53_708_928 and
            expected['expanded_bytes']==10_774_955_452,'Exact stage read budget differs')
    items,root,check=qualified_items(repo,binding,tick=tick)
    reader=VolumeReboundReferences if extended and plan['reference_policy']=='fresh_native_references_volume_rebound_v2' else NativeReferences
    return StagedReferences(items,root,check,plan,reader=reader)
