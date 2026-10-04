"""Frozen-cohort localizer consumer, with a scoped read-only source binding.

The only public factory resolves the cohort before opening any source payload. Historical
ID lists and caller-supplied image paths are not model input APIs here. No persistent cache.
"""
from copy import deepcopy
import gzip
import io
import json
import os
from pathlib import Path
import nibabel as nib
import numpy as np
import yaml

from scripts.diagnostics.localizer_content_verify import open_relative,signature,load_spec
from scripts.diagnostics.storage_setup import disk_info
from src.data.binary_label_policy import decode_binary,APPROVED_POLICY
from src.data.cohort_registry import resolve_inputs,COHORT_ID,MEMBERS
from src.data.manifest_records import digest
from src.data.source_inventory_records import require
from src.data.localizer_preprocessing import preprocess,validate_recipe
from src.operations.storage_roots import cohort_store


class SourceBinding:
    def __init__(self,root,rows,check):
        self.root=Path(root);self.rows={r['uri']:r for r in rows};self.check=check

    def image(self,reference,*,study_id,kind):
        self.check()
        require(reference['root_alias']=='followup_source','Unsupported source alias')
        row=self.rows.get(reference['uri'])
        require(row is not None and row['study_id']==study_id and row['kind']==kind and row['protected_role']=='train',
                'Source outside consumed train-purpose binding')
        require(reference['content_sha256']==row['expected_content_sha256'] and reference['bytes']==row['bytes'], 'Source reference mismatch')
        require(row['bytes']<=32*1024**2,'Compressed file cap')
        fd=open_relative(self.root,row['uri'])
        try:
            expected=dict(row['observation'],bytes=row['bytes'])
            require(signature(os.fstat(fd))==expected,'Changed source identity')
            with os.fdopen(os.dup(fd),'rb') as stream:payload=stream.read(row['bytes']+1)
            require(len(payload)==row['bytes'] and digest(payload)==reference['content_sha256'],'Changed source bytes')
            require(signature(os.fstat(fd))==expected,'Source changed while reading')
            again=open_relative(self.root,row['uri'])
            try:require(signature(os.fstat(again))==expected,'Source path replaced')
            finally:os.close(again)
        finally:os.close(fd)
        with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:raw=stream.read(256*1024**2+1)
        require(len(raw)<=256*1024**2,'Expanded source cap')
        image=nib.Nifti1Image.from_bytes(raw)
        require(len(image.shape)==3 and np.prod(image.shape)<=20_000_000,'Source shape/voxel cap')
        self.check()
        return image


class LocalizerDataset:
    """Use open_localizer_dataset, not unreviewed construction, for production input."""
    def __init__(self,descriptors,binding,recipe):
        self.descriptors=deepcopy(descriptors);self.binding=binding;self.recipe=deepcopy(recipe)

    def __len__(self):return len(self.descriptors)

    def load_native(self,index):
        d=self.descriptors[index];sid=d['study_id']
        require(sid in MEMBERS and d['cohort_id']==COHORT_ID,'Wrong cohort member')
        require(d['mapping']['policy_id']==APPROVED_POLICY,'Unsupported binary policy')
        ct=self.binding.image(d['image'],study_id=sid,kind='ct')
        mask=self.binding.image(d['target'],study_id=sid,kind='pancreas')
        g=d['geometry'];a=np.asarray(g['affine_ras']).reshape(4,4)
        require(list(ct.shape)==g['shape_xyz'] and ct.shape==mask.shape,'Source grid shape changed')
        require(np.allclose(ct.affine,a,rtol=0,atol=1e-5) and np.allclose(mask.affine,a,rtol=0,atol=1e-5), 'Source affine changed')
        require(ct.header.get_xyzt_units()[0]=='mm' and mask.header.get_xyzt_units()[0] in ('mm','unknown'), 'Unsupported physical units')
        require(np.allclose(nib.affines.voxel_sizes(a),g['spacing_mm_xyz'],rtol=0,atol=1e-6),'Spacing evidence changed')
        image=ct.get_fdata(dtype=np.float32)
        require(np.isfinite(image).all(),'Nonfinite CT')
        target,decode=decode_binary(mask.get_fdata(dtype=np.float64),policy=APPROVED_POLICY)
        require(target.any(),'Frozen pancreas-present target became empty')
        return image,target,a,decode

    def __getitem__(self,index):
        image,target,a,decode=self.load_native(index)
        result=preprocess(image,a,self.recipe,target=target)
        result['provenance']=deepcopy(dict(self.descriptors[index],decode=decode))
        return result


def open_localizer_dataset(*,repo,capability_path,trusted_capability_sha256,recipe_path,trusted_recipe_sha256):
    repo=Path(repo);capbytes=Path(capability_path).read_bytes()
    require(digest(capbytes)==trusted_capability_sha256,'Unreviewed read capability')
    cap=json.loads(capbytes)
    require(cap['schema_version']=='1.0.0' and cap['approval']=='D-270' and cap['cohort_id']==COHORT_ID and cap['study_ids']==MEMBERS and
            cap['source_alias']=='followup_source' and cap['operation']=='read_only_preprocessing' and
            cap['raw_file_count']==4,'Unsupported read scope')
    recipebytes=Path(recipe_path).read_bytes();require(digest(recipebytes)==trusted_recipe_sha256==cap['recipe_file_sha256'], 'Recipe changed')
    recipe=json.loads(recipebytes);validate_recipe(recipe)
    publication=repo/'docs/capstone/operations/COHORT-PUBLICATION-CAPABILITY-2026-09-28.json'
    store=cohort_store(repo/'configs/local/roots.yaml',publication.read_bytes(),trusted_capability_sha256=cap['publication_capability_sha256'])
    descriptors=resolve_inputs(store,receipt_sha256=cap['completion_sha256'],trusted_s3_receipt_sha256=cap['s3_receipt_sha256'],
                               current_manifest_sha256=cap['manifest_sha256'])
    require([d['study_id'] for d in descriptors]==cap['study_ids'],'Resolved membership changed')
    spec=load_spec();rows=[r for r in spec['files'] if r['study_id'] in cap['study_ids']]
    require(len(rows)==4 and sum(r['bytes'] for r in rows)<=64*1024**2,'Source read budget')
    request_path=repo/cap['source_request_path'];requestbytes=request_path.read_bytes()
    require(digest(requestbytes)==cap['source_request_sha256'],'Source binding changed')
    request=json.loads(requestbytes);registry_path=repo/'configs/local/roots.yaml'
    registrybytes=registry_path.read_bytes();require(digest(registrybytes)==request['registry_sha256'],'Registry changed')
    registry=yaml.safe_load(registrybytes);domain=registry['failure_domains']['external_primary']
    root=Path(request['diagnostic_root']);mount=Path(domain['mount_path'])
    require(root.parent==Path(registry['roots']['pants_source']['acquisition_parent']) and root.is_relative_to(mount), 'Unregistered source root')
    def check():
        require(digest(registry_path.read_bytes())==request['registry_sha256'],'Registry changed during loading')
        info=disk_info(mount)
        require(mount.is_mount() and info.get('VolumeUUID')==domain['volume_uuid'] and
                info.get('FilesystemType')=='apfs' and info.get('MountPoint')==str(mount),'Wrong source volume')
        require(root.stat().st_dev==mount.stat().st_dev,'Source root changed device')
    check()
    return LocalizerDataset(descriptors,SourceBinding(root,rows,check),recipe)
