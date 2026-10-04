"""D-304 target-only native references; immutable qualifications, no CT reads."""
from copy import deepcopy
import json
from pathlib import Path
import nibabel as nib
import numpy as np
import yaml
from scripts.diagnostics.storage_setup import disk_info
from scripts.diagnostics.freeze_localizer_expansion import CAP,CAP_PIN
from src.data.twomm_cache_inputs import (COMPLETION,INPUTS,MANIFEST,REGISTRY,OPERATIONS,
    validate_bundle,descriptors,verify_live_mapping)
from src.data.localizer_expansion_v2 import BUNDLE_ID
from src.data.source_inventory_records import content_hash,require,unique
from src.data.manifest_records import digest
from src.data.bounded_nifti_audit import read_file
from src.data.binary_label_policy import decode_binary,APPROVED_POLICY
from src.data import binary_label_policy
from src.data.localizer_preprocessing_v4 import validate_recipe
from src.operations.storage_roots import cohort_store

LIMITS=dict(compressed=32*1024**2,expanded=5*1024**3,per_file_compressed=128*1024**2,
            per_file_expanded=128*1024**2,voxels=96_000_000)

class ReadBudget:
    def __init__(self,items):
        self.compressed=0;self.expanded=0;self.files=0;self.seen=set();self.pending=None
        self.expected={row['uri']:dict(row) for d in items for row in [d['rows']['pancreas']]}
        require(len(self.expected)==len(items) and 0<len(items)<=153,'Duplicate/invalid input scope')
        self.compressed_cap=sum(r['bytes'] for r in self.expected.values())
        self.expanded_cap=sum(r['expanded_bytes'] for r in self.expected.values())
        require(self.compressed_cap<=LIMITS['compressed'] and self.expanded_cap<=LIMITS['expanded'],'Cumulative source scope cap')
    def remaining(self,row):
        require(self.pending is None and row['uri'] not in self.seen and self.expected.get(row['uri'])==row,'Unscoped/repeated/pending source read')
        require(self.compressed+row['bytes']<=self.compressed_cap,'Cumulative compressed cap')
        self.pending=row['uri']
        return min(LIMITS['per_file_expanded'],self.expected[row['uri']]['expanded_bytes'])
    def record(self,r):
        require(self.pending is not None,'No pending source read');expected=self.expected[self.pending]
        require(r['compressed_bytes']==expected['bytes'] and r['expanded_bytes']==expected['expanded_bytes'],'Unexpected source byte count')
        self.compressed+=r['compressed_bytes'];self.expanded+=r['expanded_bytes'];self.files+=1
        require(self.expanded<=self.expanded_cap,'Cumulative expanded cap')
        self.seen.add(self.pending);self.pending=None


class NativeReferences:
    def __init__(self,items,root,check,budget,operation):
        require(operation in OPERATIONS,'Explicit reference role required')
        self._items=deepcopy(items);self._pins=[content_hash(d) for d in items]
        self._root=Path(root);self._check=check;self._budget=budget;self._operation=operation
        for d in items:
            require(d['operation']==operation and d['protected_role']==OPERATIONS[operation][0], 'Wrong reference role')
            require(d['target_scope']=='visible_reference_not_whole_organ','Unsupported reference scope')
    def __len__(self):return len(self._items)
    def descriptor(self,index):return deepcopy(self._items[index])
    def _read(self,row,cap):
        return read_file(self._root,row,compressed_cap=LIMITS['per_file_compressed'],
            expanded_cap=cap,voxel_cap=LIMITS['voxels'],tick=self._check)
    def load(self,index,*,operation):
        require(operation==self._operation,'Reference operation mismatch')
        require(type(index) is int and 0<=index<len(self),'Invalid reference index')
        d=self._items[index];require(content_hash(d)==self._pins[index],'Reference binding changed')
        verify_live_mapping([d],Path(binary_label_policy.__file__).read_bytes())
        row=d['rows']['pancreas'];ref=d['target']
        require(row['kind']=='pancreas' and row['study_id']==d['study_id'] and
            row['protected_role']==OPERATIONS[operation][0] and row['uri']==ref['uri'],'Reference outside role/path')
        self._check();cap=self._budget.remaining(row)
        image,receipt=self._read(row,cap)
        require(receipt['content_sha256']==ref['content_sha256'] and receipt['compressed_bytes']==ref['bytes'],
                'Reference differs from qualified source')
        self._budget.record(receipt)
        g=d['geometry'];affine=np.asarray(g['affine_ras']).reshape(4,4)
        require(list(image.shape)==g['shape_xyz'] and np.allclose(image.affine,affine,rtol=0,atol=1e-5),
                'Reference geometry differs')
        require(image.header.get_xyzt_units()[0] in ('mm','unknown') and
            np.allclose(nib.affines.voxel_sizes(affine),g['spacing_mm_xyz'],rtol=0,atol=1e-6),'Reference physical geometry differs')
        target,decoded=decode_binary(image.get_fdata(dtype=np.float64),policy=APPROVED_POLICY)
        require(target.any(),'Qualified positive reference became empty');self._check()
        return target,affine,dict(descriptor=deepcopy(d),file=receipt,decode=decoded,
            scope='training_fit_diagnostic' if operation=='optimizer' else 'development_validation')

def open_native_references(*,repo,capability_bytes,trusted_capability_sha256,recipe_bytes,trusted_recipe_sha256,batch_id,tick=lambda:None):
    """One verified bundle resolution, two explicitly role-bound views, shared read budget."""
    repo=Path(repo);require(digest(capability_bytes)==trusted_capability_sha256,'Unreviewed input capability')
    cap=json.loads(capability_bytes);require(cap['approval']=='D-304' and cap['schema_version']=='1.0.0' and cap['operation']=='score_native_pancreas_references' and cap['limits']==LIMITS,'Unsupported read scope')
    require(cap['completion_sha256']==COMPLETION and cap['inputs_sha256']==INPUTS and cap['manifest_sha256']==MANIFEST and cap['source_file_count']==153,'Wrong frozen cohort scope')
    require(digest(recipe_bytes)==trusted_recipe_sha256==cap['recipe_sha256'],'Recipe changed')
    recipe=json.loads(recipe_bytes);validate_recipe(recipe)
    all_items,root,check=resolve_qualified_scope(repo,cap,tick=tick)
    batches=unique(cap['batches'],'batch_id');require(batch_id in batches,'Unknown batch')
    flat=[sid for batch in batches.values() for sid in batch['study_ids']]
    require(len(flat)==153 and len(set(flat))==153 and set(flat)=={d['study_id'] for v in all_items.values() for d in v},'Incomplete/overlapping batches')
    selected=set(batches[batch_id]['study_ids']);items={op:[d for d in v if d['study_id'] in selected] for op,v in all_items.items()}
    budget=ReadBudget([d for v in items.values() for d in v]);datasets={}
    for operation,rows in items.items():
        verify_live_mapping(rows,Path(binary_label_policy.__file__).read_bytes())
        datasets[operation]=NativeReferences(rows,root,check,budget,operation)
    check();return datasets,budget


def resolve_qualified_scope(repo,cap,*,tick=lambda:None):
    """Read-only cohort/storage verification shared by separately authorized consumers."""
    store=cohort_store(repo/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN)
    files,_=store.resolve(BUNDLE_ID,receipt_sha256=COMPLETION,validate=validate_bundle)
    derived=json.loads(files['derived.json']);inputs=json.loads(files['inputs.json']);require(content_hash(derived['manifest'])==MANIFEST,'Manifest changed')
    registry_path=repo/'configs/local/roots.yaml';raw=registry_path.read_bytes();require(digest(raw)==REGISTRY==cap['registry_sha256'],'Registry changed')
    registry=yaml.safe_load(raw);domain=registry['failure_domains']['external_primary'];mount=Path(domain['mount_path']);root=Path(cap['source_root'])
    require(root.parent==Path(registry['roots']['pants_source']['acquisition_parent']) and root.name=='extraction-3b1cd6110811-20260922' and root.resolve(strict=True)==root,'Unregistered source root')
    info=disk_info(mount);require(mount.is_mount() and info.get('VolumeUUID')==domain['volume_uuid']==cap['volume_uuid'] and info.get('FilesystemType')=='apfs' and info.get('MountPoint')==str(mount),'Wrong source volume')
    device=mount.stat().st_dev
    def check():
        tick();require(digest(registry_path.read_bytes())==REGISTRY,'Registry changed during read')
        require(mount.is_mount() and mount.stat().st_dev==device and root.stat().st_dev==device,'Source mount changed')
    all_items={op:descriptors(derived,inputs,op) for op in OPERATIONS}
    require({op:[d['study_id'] for d in items] for op,items in all_items.items()}==cap['members'],'Capability membership changed')
    require({op:len(v) for op,v in all_items.items()}=={'optimizer':113,'evaluator':40},'Frozen role count differs')
    check();return all_items,root,check
