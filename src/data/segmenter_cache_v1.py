"""Versioned three-class derived input cache; no source reads or optimizer permission."""
from copy import deepcopy
from io import BytesIO
import json
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require,content_hash
from src.data import segmenter_geometry_v1 as geometry
from src.data.segmenter_geometry_loader_v1 import checked_descriptor

VERSION='segmenter-input-cache-1'


def checked_binding(b,pin):
    require(content_hash(b)==pin,'Independent cache binding changed')
    require(set(b)=={'schema_version','cohort_completion_sha256','descriptor_sha256','geometry_acceptance_sha256','records','entries','model_updates_allowed'},'Binding fields differ')
    require(b['schema_version']==VERSION and b['model_updates_allowed'] is False,'Wrong cache task/permission')
    for k in ('cohort_completion_sha256','descriptor_sha256','geometry_acceptance_sha256'):
        require(isinstance(b[k],str) and len(b[k])==64 and all(c in '0123456789abcdef' for c in b[k]),'Invalid lineage pin')
    records=b['records'];require(set(records)=={'optimizer','evaluator'},'Descriptor role inventory differs')
    order=[(op,d['study_id']) for op in ('optimizer','evaluator') for d in records[op]]
    require(order and len(order)==len(set(sid for _,sid in order)) and len(order)<=7,'Empty/duplicate/excess membership')
    require([(e['operation'],e['descriptor']['study_id']) for e in b['entries']]==order,'Entry order/membership differs')
    for e in b['entries']:
        require(set(e)=={'operation','descriptor','transform','transform_sha256','fidelity','tensor_class_counts'},'Entry fields differ')
        d=e['descriptor'];require(d==checked_descriptor(records,b['descriptor_sha256'],d['study_id'],e['operation']),'Wrong qualified descriptor')
        t=e['transform'];geometry.validate_record(t,e['transform_sha256'])
        require(t['recipe']==geometry.recipe() and t['roi_origin']=='provided_pancreas_reference' and t['source_identity']==dict(study_id=d['study_id'],ct_sha256=d['image']['content_sha256']) and t['source_shape']==d['geometry']['shape_xyz'] and t['source_affine']==np.asarray(d['geometry']['affine_ras']).reshape(4,4).tolist(),'Geometry/source lineage differs')
        f=e['fidelity'];require(f['lesion_target_state']==d['lesion_target_state'] and f['source_arrays_changed'] is False,'Fidelity target state differs')
        counts=e['tensor_class_counts'];require(isinstance(counts,list) and len(counts)==3 and all(type(n)==int and n>=0 for n in counts) and sum(counts)==144**3,'Invalid class counts')
        require(counts[1]==f['metrics']['pancreas_parenchyma']['tensor_voxels'] and counts[2]==f['metrics']['lesion']['tensor_voxels'] and bool(counts[2])==(d['lesion_target_state']=='positive'),'Tensor/fidelity counts differ')
    return len(order)*144**3*5


def arrays(image,target,entry):
    x=np.asarray(image);y=np.asarray(target)
    require(x.dtype==np.float32 and x.shape==(1,144,144,144) and np.isfinite(x).all() and x.min()>=0 and x.max()<=1,'Invalid normalized image dtype/grid/values')
    require(y.dtype==np.uint8 and y.shape==(144,144,144) and np.isin(y,[0,1,2]).all(),'Invalid three-class target dtype/grid/values')
    require(np.bincount(y.ravel(),minlength=3).tolist()==entry['tensor_class_counts'],'Changed target class counts')
    return x,y


def encode(a):
    stream=BytesIO();np.save(stream,a,allow_pickle=False);return stream.getvalue()


def decode(raw,kind):
    require(isinstance(raw,bytes) and len(raw)<=144**3*4+1024,'Serialized array cap')
    stream=BytesIO(raw);require(np.lib.format.read_magic(stream)==(1,0),'Unsupported NPY format')
    shape,fortran,dtype=np.lib.format.read_array_header_1_0(stream,max_header_size=512)
    expected_shape=(1,144,144,144) if kind=='image' else (144,144,144)
    expected_dtype=np.dtype('float32') if kind=='image' else np.dtype('uint8')
    require(kind in ('image','target') and shape==expected_shape and dtype==expected_dtype and fortran is False,'NPY dtype/shape/order differs')
    require(len(raw)==stream.tell()+int(np.prod(shape))*dtype.itemsize,'NPY truncated/trailing bytes')
    a=np.load(BytesIO(raw),allow_pickle=False)
    if kind=='image':require(np.isfinite(a).all() and a.min()>=0 and a.max()<=1,'Invalid cached image values')
    else:require(np.isin(a,[0,1,2]).all(),'Invalid cached target codes')
    return a


def names(index):return {k:f'case-{index:02d}-{k}.npy' for k in ('image','target')}


def validate(files,binding,pin):
    payload=checked_binding(binding,pin)
    expected={'binding.json','production.json'}|{n for i in range(len(binding['entries'])) for n in names(i).values()}
    require(set(files)==expected and all(isinstance(v,bytes) for v in files.values()),'Cache member inventory differs')
    require(files['binding.json']==canonical(binding),'Stored binding differs')
    p=json.loads(files['production.json']);require(set(p)=={'schema_version','binding_sha256','request_sha256','code_pins','runtime','source_counts','cases','model_updates','source_arrays_read'},'Production fields differ')
    require(p['schema_version']==VERSION and p['binding_sha256']==pin and type(p['model_updates']) is int and p['model_updates']==0,'Wrong production domain')
    require(len(p['cases'])==len(binding['entries']) and type(p['source_arrays_read']) is int and p['source_arrays_read']==3*len(binding['entries']),'Production case/read count differs')
    require(isinstance(p['request_sha256'],str) and len(p['request_sha256'])==64 and all(v in '0123456789abcdef' for v in p['request_sha256']) and isinstance(p['code_pins'],dict) and isinstance(p['runtime'],dict),'Invalid production lineage')
    require(set(p['source_counts'])=={'hash_bytes','decode_bytes','expanded_bytes'} and all(type(n) is int and n>=0 for n in p['source_counts'].values()),'Invalid source accounting')
    inventories=[]
    for i,(e,row) in enumerate(zip(binding['entries'],p['cases'])):
        nm=names(i);x=decode(files[nm['image']],'image');y=decode(files[nm['target']],'target');arrays(x,y,e)
        expected_row=dict(study_id=e['descriptor']['study_id'],protected_role=e['descriptor']['protected_role'],transform_sha256=e['transform_sha256'],tensor_class_counts=e['tensor_class_counts'],files={k:dict(name=n,bytes=len(files[n]),sha256=digest(files[n])) for k,n in nm.items()})
        require(row==expected_row,'Production case/array identity differs');inventories.append(row)
    return dict(schema_version=VERSION,binding_sha256=pin,payload_bytes=payload,cases=inventories,model_updates=0)


class InputCache:
    def __init__(self,files,binding,pin):
        validate(files,binding,pin);self._files=dict(files);self._binding=deepcopy(binding);self._pin=pin
        self._hashes={n:digest(v) for n,v in files.items()}

    def get(self,study_id,*,role,operation):
        require(operation in ('inference','evaluator'),'Optimizer/wrong operation closed in cache readiness')
        require(role in ('train','validation'),'Explicit protected role required')
        checked_binding(self._binding,self._pin)
        matches=[(i,e) for i,e in enumerate(self._binding['entries']) if e['descriptor']['study_id']==study_id and e['descriptor']['protected_role']==role]
        require(len(matches)==1,'Held/absent/wrong-role member')
        i,e=matches[0];nm=names(i)
        for n in ('binding.json','production.json',nm['image']) if operation=='inference' else ('binding.json','production.json',nm['image'],nm['target']):
            require(digest(self._files[n])==self._hashes[n],'In-memory/cache bytes changed')
        result=dict(image=decode(self._files[nm['image']],'image'),transform=deepcopy(e['transform']),transform_sha256=e['transform_sha256'],study_id=study_id,protected_role=role)
        if operation=='evaluator':result['target']=decode(self._files[nm['target']],'target')
        return result
