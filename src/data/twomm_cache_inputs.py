"""D-300 role-specific broader cohort input factory; no optimizer or source mutation.

The public factory resolves a completed independently pinned bundle. Internal constructors
support synthetic tests, not permission to supply arbitrary paths to production training.
"""
from copy import deepcopy
import json
from pathlib import Path
import nibabel as nib
import numpy as np
import yaml
from scripts.diagnostics.storage_setup import disk_info
from scripts.diagnostics.freeze_localizer_expansion import CAP, CAP_PIN
from src.data.localizer_expansion_v2 import BUNDLE_ID
from src.data.manifest_records import digest
from src.data.source_inventory_records import content_hash,require,unique
from src.data.bounded_nifti_audit import read_file
from src.data.binary_label_policy import decode_binary,APPROVED_POLICY
from src.data import binary_label_policy
from src.data.localizer_preprocessing_v4 import preprocess,validate_recipe,plan_geometry
from src.operations.storage_roots import cohort_store

COMPLETION='b401fa1ba8b0ab25dbe6abfe575e60d03dba438db493175c5d5b4bd0b03293b7'
INPUTS='2c6c723cf4658d8d4926d07b804f20abc10b1afd83485f36adab4d436a809785'
MANIFEST='3f1a54f202773dd2ed7fe8c274385b52f53e8ececedd5c1fe2ec4a07d5065558'
REGISTRY='46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788'
OPERATIONS={'optimizer':('train','training_target'),'evaluator':('validation','evaluation_reference')}
LIMITS=dict(compressed=6*1024**3,expanded=16*1024**3,per_file_compressed=128*1024**2,per_file_expanded=512*1024**2,voxels=96_000_000)


DERIVED='b0f1c625728603ce87841d5c0ce7ad5397574da04dd5e7ca4814c5ef462ca29f'


def validate_bundle(files):
    # These are independent D-294 publication AND fresh-process replay pins, not hashes
    # taken from a caller-supplied manifest. Exact same bytes retain that qualification.
    require(set(files)=={'inputs.json','derived.json'},'Wrong bundle inventory')
    require(digest(files['inputs.json'])==INPUTS and digest(files['derived.json'])==DERIVED,'Published cohort bytes changed')
    # Return the independently retained D-294 validation attestation for these EXACT bytes.
    # ArtifactStore compares this to the immutable completion receipt's validation field.
    return dict(bundle_id=BUNDLE_ID,manifest_sha256=MANIFEST,qualified_count=153,held_count=23,
        executable_counts={'train':113,'validation':40},protected_counts={'train':7200,'validation':1800,'test':901},
        prior_issues_preserved=23,source_arrays_opened=False)


class ReadBudget:
    def __init__(self,items):
        self.compressed=0;self.expanded=0;self.files=0;self.seen=set();self.pending=None
        self.expected={row['uri']:dict(row) for d in items for row in d['rows'].values()}
        require(len(self.expected)==2*len(items) and 0<len(items)<=153,'Duplicate/invalid input scope')
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


def descriptors(derived,inputs,operation):
    require(operation in OPERATIONS,'Explicit optimizer/evaluator operation required')
    role,use=OPERATIONS[operation];m=derived['manifest']
    cohorts=[c for c in derived['cohorts'] if c['protected_role']==role]
    require(len(cohorts)==1,'Wrong cohort role')
    c=cohorts[0];require(c['capability']=='executable','Protection-only cohort')
    require([x['study_id'] for x in c['members']]==derived['accounting']['executable_ids'][role],'Frozen member accounting differs')
    studies=unique(m['studies'],'study_id');annotations=unique(m['annotations'],'annotation_id');qs=unique(derived['qualifications'],'qualification_id')
    selection=json.loads(inputs['selection_files']['selection.json']);manifest_pin=content_hash(m);candidates=unique(selection['candidates'][role],'study_id')
    result=[]
    for member in c['members']:
        sid=member['study_id'];q=qs.get(member['qualification']['id']);a=annotations.get(member['annotation']['id']);s=studies[sid]
        require(member['protected_role']==role and q is not None and q['protected_role']==role and q['outcome']=='qualified' and q['study_id']==sid,'Held or wrong-role member')
        require(q['purpose']=={'optimizer':'pancreas_localizer_training','evaluator':'pancreas_localizer_validation'}[operation],'Qualification purpose differs')
        require(a is not None and a['study_id']==sid and a['status']=='eligible' and a['allowed_uses']==[use] and q['annotation_id']==a['annotation_id'],'Purpose-specific annotation permission required')
        require(member['qualification']['sha256']==content_hash(q) and member['annotation']['sha256']==content_hash(a),'Member identity changed')
        candidate=candidates[sid];rows=deepcopy(unique(candidate['inventory_inputs'],'kind'))
        facts=json.loads(derived['evidence'][a['label_encoding']['audit_file']['content_sha256']])
        for f in facts['files']:rows[f['kind']]['expanded_bytes']=f['expanded_bytes']
        require(set(rows)=={'ct','pancreas'},'Exact source pair required')
        refs={'ct':s['image'],'pancreas':a['file']}
        for kind,row in rows.items():
            ref=refs[kind]
            require(row['study_id']==sid and row['protected_role']==role and row['uri']==ref['uri'] and row['bytes']==ref['bytes'] and ref['root_alias']=='followup_source','Source outside role binding')
        result.append(dict(study_id=sid,protected_role=role,operation=operation,cohort_id=c['cohort_id'],geometry=s['geometry'],mapping=a['label_encoding']['mapping'],
            image=refs['ct'],target=refs['pancreas'],rows=rows,manifest_sha256=manifest_pin,qualification=deepcopy(member['qualification']),target_scope='visible_reference_not_whole_organ',
            observations=[i['message'] for i in m['issues'] if i['issue_id'] in s['issue_ids']]))
    return result


def verify_live_mapping(items,implementation_bytes):
    pin=digest(implementation_bytes)
    require(all(d['mapping']['policy_id']==APPROVED_POLICY and d['mapping']['policy_sha256']==pin for d in items),'Live binary implementation differs from qualified lineage')


class ExpandedDataset:
    def __init__(self,items,root,check,recipe,budget,operation):
        require(operation in OPERATIONS,'Explicit operation required');validate_recipe(recipe)
        self._items=deepcopy(items);self._pins=[content_hash(x) for x in self._items]
        self._root=Path(root);self._check=check;self._recipe=deepcopy(recipe);self._recipe_pin=content_hash(recipe);self._budget=budget;self._operation=operation
        for d in self._items:
            require(d['operation']==operation and d['protected_role']==OPERATIONS[operation][0],'Wrong consumer role')
            plan_geometry(d['geometry']['shape_xyz'],d['geometry']['affine_ras'] if np.asarray(d['geometry']['affine_ras']).shape==(4,4) else np.asarray(d['geometry']['affine_ras']).reshape(4,4),recipe)
    def __len__(self):return len(self._items)
    @property
    def recipe(self):return deepcopy(self._recipe)
    def descriptor(self,index):return deepcopy(self._items[index])
    def load_native(self,index,*,operation):
        require(operation==self._operation,'Consumer operation/role mismatch')
        require(type(index) is int and 0<=index<len(self),'Member index outside frozen cohort')
        d=self._items[index];require(content_hash(d)==self._pins[index] and content_hash(self._recipe)==self._recipe_pin,'Input controls changed')
        require(d['mapping']['policy_id']==APPROVED_POLICY,'Unsupported target mapping')
        self._check();images={};receipts=[]
        for kind,ref in [('ct',d['image']),('pancreas',d['target'])]:
            row=d['rows'][kind];require(row['protected_role']==OPERATIONS[operation][0] and row['uri']==ref['uri'],'Changed role/path binding')
            expanded_cap=self._budget.remaining(row)
            im,receipt=read_file(self._root,row,compressed_cap=LIMITS['per_file_compressed'],expanded_cap=expanded_cap,voxel_cap=self._recipe['max_source_voxels'],tick=self._check)
            require(receipt['content_sha256']==ref['content_sha256'] and receipt['compressed_bytes']==ref['bytes'],'Source bytes differ from qualified reference')
            self._budget.record(receipt);images[kind]=im;receipts.append(dict(kind=kind,**receipt));self._check()
        ct,mask=images['ct'],images['pancreas'];g=d['geometry'];affine=np.asarray(g['affine_ras']).reshape(4,4)
        require(list(ct.shape)==g['shape_xyz'] and ct.shape==mask.shape,'Changed source shape')
        require(np.allclose(ct.affine,affine,rtol=0,atol=1e-5) and np.allclose(mask.affine,affine,rtol=0,atol=1e-5),'Changed source affine')
        require(ct.header.get_xyzt_units()[0]=='mm' and mask.header.get_xyzt_units()[0] in ('mm','unknown'),'Unsupported physical units')
        require(np.allclose(nib.affines.voxel_sizes(affine),g['spacing_mm_xyz'],rtol=0,atol=1e-6),'Changed physical spacing')
        image=ct.get_fdata(dtype=np.float32);require(np.isfinite(image).all(),'Nonfinite CT')
        target,decode=decode_binary(mask.get_fdata(dtype=np.float64),policy=APPROVED_POLICY)
        require(target.any(),'Positive reference became empty');self._check()
        return image,target,affine,dict(decode=decode,files=receipts,descriptor=deepcopy(d))
    def load(self,index,*,operation):
        image,target,a,provenance=self.load_native(index,operation=operation)
        result=preprocess(image,a,self._recipe,target=target);result['provenance']=provenance;self._check();return result


def open_expanded_inputs(*,repo,capability_bytes,trusted_capability_sha256,recipe_bytes,trusted_recipe_sha256,batch_id,tick=lambda:None):
    """One verified bundle resolution, two explicitly role-bound views, shared read budget."""
    repo=Path(repo);require(digest(capability_bytes)==trusted_capability_sha256,'Unreviewed input capability')
    cap=json.loads(capability_bytes);require(cap['approval']=='D-300' and cap['schema_version']=='1.0.0' and cap['operation']=='build_persisted_twomm_cache' and cap['limits']==LIMITS,'Unsupported read scope')
    require(cap['completion_sha256']==COMPLETION and cap['inputs_sha256']==INPUTS and cap['manifest_sha256']==MANIFEST and cap['source_file_count']==306,'Wrong frozen cohort scope')
    require(digest(recipe_bytes)==trusted_recipe_sha256==cap['recipe_sha256'],'Recipe changed')
    recipe=json.loads(recipe_bytes);validate_recipe(recipe)
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
    batches=unique(cap['batches'],'batch_id');require(batch_id in batches,'Unknown batch')
    flat=[sid for batch in batches.values() for sid in batch['study_ids']]
    require(len(flat)==153 and len(set(flat))==153 and set(flat)=={d['study_id'] for v in all_items.values() for d in v},'Incomplete/overlapping batches')
    selected=set(batches[batch_id]['study_ids']);items={op:[d for d in v if d['study_id'] in selected] for op,v in all_items.items()}
    budget=ReadBudget([d for v in items.values() for d in v]);datasets={}
    for operation,rows in items.items():
        verify_live_mapping(rows,Path(binary_label_policy.__file__).read_bytes())
        datasets[operation]=ExpandedDataset(rows,root,check,recipe,budget,operation)
    check();return datasets,budget
