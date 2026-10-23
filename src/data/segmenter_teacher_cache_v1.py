"""Train-only native-region probability cache; bounded uint16 quantization.

No teacher inference or CT reading here. Cache construction requires separately
qualified world-coordinate reconstruction. All full-region voxels must have a
teacher probability; unavailable predictions are not silently filled with zero.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import numpy as np
from scipy import ndimage

from src.data.manifest_records import canonical, digest
from src.data.segmenter_teacher_targets_v1 import HASH_FIELDS
from src.data.segmenter_physical_windows_v1 import coordinate_map

SCHEMA='native-region-lesion-probabilities-uint16-v1'
QUANTIZATION_ERROR=0.5/65535 + np.finfo(np.float32).eps


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def identity_for(name,small,common):
    required={'teacher_sha256','teacher_config_sha256','teacher_mapping_sha256',
              'preprocessing_sha256','control_sha256'}
    if set(common)!=required:raise ValueError('Incomplete common teacher identity')
    if not isinstance(name,str) or not re.fullmatch('[A-Za-z0-9_-]+',name):raise ValueError('Unsafe case name')
    result=dict(case_id=name,role='train',**common,
        source_image_sha256=small['source_sha256']['ct'],
        source_geometry_sha256=digest(canonical(small['parent_geometry'])),
        grid_sha256=digest(canonical(small['geometry'])))
    if any(not isinstance(result[k],str) or not re.fullmatch('[0-9a-f]{64}',result[k]) for k in HASH_FIELDS):
        raise ValueError('Teacher provenance must be SHA256')
    return result


def encode(probability):
    if (not isinstance(probability,np.ndarray) or probability.dtype!=np.float32 or probability.ndim!=3 or
        min(probability.shape)<1 or not np.isfinite(probability).all() or probability.min()<0 or probability.max()>1):
        raise ValueError('Finite complete float32 probability field required')
    encoded=np.rint(probability*65535.).astype(np.uint16)
    error=float(np.max(np.abs(encoded.astype(np.float32)/65535.-probability)))
    if error>QUANTIZATION_ERROR:raise ValueError('Quantization fidelity failed')
    return encoded,error


def write_member(root,name,probability,identity):
    if identity.get('role')!='train' or identity.get('case_id')!=name or not re.fullmatch('[A-Za-z0-9_-]+',name):
        raise ValueError('Only named training targets can be cached')
    root=Path(root);root.mkdir(exist_ok=True)
    values,error=encode(probability)
    path=root/(name+'.npz')
    with path.open('xb') as stream:np.savez_compressed(stream,probability=values)
    return dict(schema=SCHEMA,identity=deepcopy(identity),shape=list(values.shape),
        storage='uint16_probability_round_to_nearest_div65535',support='entire_native_region',
        payload_sha256=sha(path),bytes=path.stat().st_size,max_quantization_error=error)


def sample_field(values,record,origin,*,window=144):
    if values.dtype!=np.uint16 or values.shape!=tuple(record['native_shape']):raise ValueError('Native teacher grid mismatch')
    if type(window) is not int or window<1 or len(origin)!=3 or any(type(o) is not int or o<0 or o>max(0,n-window)
            for o,n in zip(origin,record['shape'])):raise ValueError('Invalid teacher window origin')
    valid_shape=[min(window,n-o) for n,o in zip(record['shape'],origin)]
    coords=coordinate_map(origin,valid_shape,record['factors'])
    # Decode only the local interpolation neighborhood, not another dense fine grid.
    low=np.maximum(0,np.floor(coords.reshape(3,-1).min(1)).astype(int))
    high=np.minimum(values.shape,np.ceil(coords.reshape(3,-1).max(1)).astype(int)+1)
    low=np.minimum(low,np.asarray(values.shape)-1);high=np.maximum(high,low+1)
    subset=values[tuple(slice(l,h) for l,h in zip(low,high))].astype(np.float32)/65535.
    local=ndimage.map_coordinates(subset,coords-low[:,None,None,None],order=1,mode='nearest',prefilter=False)
    q=np.zeros((window,)*3,np.float32);support=np.zeros(q.shape,bool)
    slices=tuple(slice(0,n) for n in valid_shape);q[slices]=local;support[slices]=True
    return q,support


class TeacherTargetStore:
    def __init__(self,root,manifest_sha256,*,control,common_identity,qualification_only=False):
        self.root=Path(root);self.pin=manifest_sha256
        if sha(self.root/'manifest.json')!=self.pin:raise ValueError('Teacher manifest pin')
        self.manifest=json.loads((self.root/'manifest.json').read_text())
        if self.manifest['schema']!=SCHEMA or self.manifest['control_sha256']!=digest(canonical(control)):
            raise ValueError('Teacher manifest control mismatch')
        self.train=set(control['train']);members=set(self.manifest['members'])
        if not members or not members<=self.train:raise ValueError('Protected role in teacher cache')
        if not qualification_only and (members!=self.train or self.manifest['complete'] is not True):
            raise ValueError('Incomplete teacher coverage')
        if common_identity['control_sha256']!=digest(canonical(control)):
            raise ValueError('Teacher common control differs')
        self.common=deepcopy(common_identity);self.control=deepcopy(control)
        self.qualification_only=qualification_only
        self.memory_pin=digest(canonical(dict(manifest=self.manifest,common=self.common,
            control=self.control,train=sorted(self.train),qualification_only=qualification_only)))

    def window(self,name,small,record,origin,*,role='train',operation='optimizer',window=144):
        if self.memory_pin!=digest(canonical(dict(manifest=self.manifest,common=self.common,
                control=self.control,train=sorted(self.train),qualification_only=self.qualification_only))):
            raise ValueError('Teacher in-memory admission changed')
        if role!='train' or operation!='optimizer' or name not in self.train:raise ValueError('Training optimizer targets only')
        if sha(self.root/'manifest.json')!=self.pin:raise ValueError('Teacher manifest changed')
        member=self.manifest['members'][name]
        expected=identity_for(name,small,self.common)
        if (member['schema']!=SCHEMA or member['identity']!=expected or
            member['shape']!=list(small['geometry']['shape']) or member['support']!='entire_native_region' or
            member['storage']!='uint16_probability_round_to_nearest_div65535' or
            not 0<=member['max_quantization_error']<=QUANTIZATION_ERROR):
            raise ValueError('Teacher case/grid/source/encoding mismatch')
        if record['native']!=small['geometry']:raise ValueError('Student/teacher native geometry mismatch')
        path=self.root/(name+'.npz')
        if sha(path)!=member['payload_sha256']:raise ValueError('Teacher payload changed')
        with np.load(path,allow_pickle=False) as data:
            if data.files!=['probability']:raise ValueError('Unexpected teacher payload')
            values=data['probability']
        q,valid=sample_field(values,record,origin,window=window)
        # A quantization-uncertain binary decision must not become an agreement
        # merely because uint16 cannot represent 0.5 exactly. Treat this tiny
        # interval as tied for KD only; supervised targets remain untouched.
        tied=valid & (np.abs(q-.5)<=QUANTIZATION_ERROR)
        q[tied]=.5
        return q,valid,dict(manifest_sha256=self.pin,payload_sha256=member['payload_sha256'],
            identity_sha256=digest(canonical(expected)),max_quantization_error=member['max_quantization_error'],
            quantization_uncertain_voxels=int(tied.sum()),agreement_deadband=QUANTIZATION_ERROR)
