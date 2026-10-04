"""Separate qualified optimizer/evaluator boundary; old readiness cache stays closed."""
from copy import deepcopy
import json
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import content_hash,require
from src.data import segmenter_cache_v1 as cache,segmenter_geometry_loader_v1 as loader
_TOKEN=object()


def target_metadata(y):
    from scipy import ndimage
    labels,n=ndimage.label(y==2,structure=np.ones((3,3,3),np.uint8));counts=np.bincount(labels.ravel(),minlength=n+1);boxes=ndimage.find_objects(labels,max_label=n)
    return dict(class_counts=np.bincount(y.ravel(),minlength=3).tolist(),components=[dict(component_id=i,native_voxels=int(counts[i]),bounds_xyz_half_open=[[v.start,v.stop] for v in box],source_boundary_contact=any(v.start==0 or v.stop==y.shape[k] for k,v in enumerate(box))) for i,box in enumerate(boxes,1)])



class Batch:
    def __init__(self,token,*,study_id,role,operation,image,target,control_sha256):
        require(token is _TOKEN,'Only a checked input provider can seal batches')
        self.study_id=study_id;self.role=role;self.operation=operation;self.control_sha256=control_sha256
        self.image=np.ascontiguousarray(image).copy();self.target=None if target is None else np.ascontiguousarray(target).copy()
        self._hashes=self.hashes();self._provenance=(study_id,role,operation,control_sha256)
    def hashes(self):return dict(image=digest(cache.encode(self.image)),target=None if self.target is None else digest(cache.encode(self.target)))
    def checked(self,control_sha256,operation,study_id):
        require((self.study_id,self.role,self.operation,self.control_sha256)==self._provenance and self.control_sha256==control_sha256 and self.operation==operation and self.study_id==study_id and self.hashes()==self._hashes,'Wrong/mutated batch provenance')
        require(operation!='optimizer' or self.role=='train','Evaluator batch cannot optimize');return self.image,self.target


class QualifiedInputs:
    def __init__(self,token,session,files,binding,pin,reference):
        require(token is _TOKEN and type(session) is loader.ResolvedInputs,'Fresh registered ancestry replay required')
        cache.validate(files,binding,pin);require(session.records==binding['records'] and binding['cohort_completion_sha256']==loader.COMPLETION and binding['descriptor_sha256']==loader.DESCRIPTORS,'Wrong registered cache ancestry')
        require(len(binding['records']['optimizer'])==6 and len(binding['records']['evaluator'])==1,'Exact six/one training input scope')
        self._session=session;self._files=dict(files);self._binding=deepcopy(binding);self._pin=pin;self._hashes={n:digest(v) for n,v in files.items()}
        self.control=dict(target_metadata={e['descriptor']['study_id']:target_metadata(cache.decode(files[cache.names(i)['target']],'target')) for i,e in enumerate(binding['entries'])},domain='qualified_real_cache',cache_reference=deepcopy(reference),binding_sha256=pin,cohort_completion_sha256=loader.COMPLETION,descriptor_sha256=loader.DESCRIPTORS,geometry_acceptance_sha256=binding['geometry_acceptance_sha256'],train=[d['study_id'] for d in binding['records']['optimizer']],validation=[d['study_id'] for d in binding['records']['evaluator']],member_sha256=self._hashes,roi_source='provided_pancreas_reference',jitter='none',original_arrays_read=0)
    def get(self,study_id,*,role,operation):
        require(operation in ('optimizer','evaluator','inference') and role in ('train','validation'),'Explicit supported role/operation')
        cache.checked_binding(self._binding,self._pin);require(self._session.records==self._binding['records'],'Replayed roles changed')
        op='optimizer' if role=='train' else 'evaluator';d=self._session.select(study_id,op);require(d['protected_role']==role and (operation!='optimizer' or role=='train'),'Wrong optimizer role')
        found=[(i,e) for i,e in enumerate(self._binding['entries']) if e['descriptor']==d];require(len(found)==1,'Absent/held cache member');i,e=found[0];nm=cache.names(i)
        needed=['binding.json','production.json',nm['image']]+([] if operation=='inference' else [nm['target']])
        for n in needed:require(digest(self._files[n])==self._hashes[n],'Cached payload mutated')
        x=cache.decode(self._files[nm['image']],'image');y=None if operation=='inference' else cache.decode(self._files[nm['target']],'target')
        if y is not None:cache.arrays(x,y,e)
        return Batch(_TOKEN,study_id=study_id,role=role,operation=operation,image=x,target=y,control_sha256=digest(canonical(self.control)))


def resolve_qualified():
    # Accepted producer resolution remains authoritative; no original-source arrays are requested.
    from scripts.diagnostics import segmenter_cache_qualification as c
    session=loader.resolve_registered();raw=c.DEST.joinpath('request.json').read_bytes();require(digest(raw)=='d84cdcdc828410ed4603dccf1bab29ecf6d0e9154f9a4f6f3f9f9cd0bc613364','Accepted cache request changed');req=json.loads(raw)
    # Read the accepted review's reference rather than infer it from a label.
    p=c.ROOT/'SEGMENTER-CACHE-REVIEW-20261002/accepted-cache.json';accept=json.loads(p.read_bytes());require(digest(p.read_bytes())=='8b21315b14e38a6f582964a274d430ce768af9fb8348c8858c9ece62221125f3','Accepted cache review changed')
    ref=dict(artifact_id=accept['cache_artifact_id'],receipt_sha256=accept['cache_completion_sha256'],derivation_sha256=accept['request_sha256']);files,_=c.store().resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:c.validate_production(f,req,digest(raw)))
    return QualifiedInputs(_TOKEN,session,files,req['binding'],req['binding_sha256'],ref)


class InventedInputs:
    def __init__(self,size):
        require(size in (24,144),'Invented shape envelope');self.size=size
        from src.training.segmenter_session_v1 import NAMES,fixture
        self._names=list(NAMES)+['sparse'];self._arrays={f'invented-train-{i}':fixture(n,size) for i,n in enumerate(self._names)};self._arrays['invented-validation']=fixture('multiple',size)
        self.control=dict(target_metadata={n:target_metadata(y.numpy().astype(np.uint8)) for n,(x,y) in self._arrays.items()},domain='invented_arrays_only',fixture_version='class_cues_six_members_v1',size=size,train=[f'invented-train-{i}' for i in range(6)],validation=['invented-validation'],member_sha256={n:dict(image=digest(cache.encode(x.numpy())),target=digest(cache.encode(y.numpy().astype(np.uint8)))) for n,(x,y) in self._arrays.items()},roi_source='invented',jitter='none',original_arrays_read=0)
    def get(self,study_id,*,role,operation):
        require(operation in ('optimizer','evaluator','inference') and role in ('train','validation') and study_id in self.control['train' if role=='train' else 'validation'] and (operation!='optimizer' or role=='train'),'Invented input role/operation')
        x,y=self._arrays[study_id];b=Batch(_TOKEN,study_id=study_id,role=role,operation=operation,image=x.numpy(),target=None if operation=='inference' else y.numpy().astype(np.uint8),control_sha256=digest(canonical(self.control)))
        expected=self.control['member_sha256'][study_id];require(b.hashes()['image']==expected['image'] and (operation=='inference' or b.hashes()['target']==expected['target']),'Invented fixture changed');return b
