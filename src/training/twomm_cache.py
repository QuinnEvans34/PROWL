"""V1 persisted 2 mm cache. Caller supplies independently frozen expected records and pin.

No source discovery, eligibility changes, or training launch. Publication is completion-last;
failed builds remain inspectable and never resume implicitly. Arrays use non-pickle NPY.
"""
from copy import deepcopy
from io import BytesIO
import json
import math
import os
from pathlib import Path
import shutil
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require,content_hash
from src.data.localizer_preprocessing_v4 import validate_recipe,geometry,plan_geometry

ROLES=('optimizer','evaluator')
PAYLOAD_CAP=4*1024**3
OVERHEAD_CAP=64*1024**2
FREE_FLOOR=100*1024**3


def checked_binding(binding,pin):
    require(digest(canonical(binding))==pin,'Expected binding changed')
    require(set(binding)=={'schema_version','review_sha256','bundle_sha256','recipe','roles'},'Binding fields differ')
    require(binding['schema_version']=='twomm-cache-1','Wrong cache version')
    for k in ('review_sha256','bundle_sha256'):
        require(isinstance(binding[k],str) and len(binding[k])==64 and all(c in '0123456789abcdef' for c in binding[k]),'Invalid evidence pin')
    recipe=binding['recipe'];validate_recipe(recipe)
    require(recipe['spacing_mm']==[2.,2.,2.] and recipe['minimum_shape']==[96]*3,'Wrong 2 mm recipe')
    require(set(binding['roles'])==set(ROLES),'Both roles required')
    seen=set();payload=0
    for role in ROLES:
        require(binding['roles'][role],'Empty role')
        for entry in binding['roles'][role]:
            require(set(entry)=={'descriptor','transform_record'},'Entry fields differ')
            d=entry['descriptor'];r=entry['transform_record'];sid=d['study_id']
            require(isinstance(sid,str) and sid and sid not in seen,'Duplicate/cross-role member');seen.add(sid)
            require(d['operation']==role and d['protected_role']=={'optimizer':'train','evaluator':'validation'}[role],'Wrong member role')
            require(r['schema_version']=='4.0.0' and r['recipe']==recipe and r['recipe_sha256']==content_hash(recipe),'Wrong transform recipe')
            require(r['record_sha256']==content_hash({k:v for k,v in r.items() if k!='record_sha256'}),'Transform hash differs')
            shape=r['processed_shape'];require(len(shape)==3 and all(type(n)==int and n>0 for n in shape) and math.prod(shape)<=16_000_000,'Processed shape cap')
            geometry(r['processed_affine'],shape);plan_geometry(r['source_shape'],r['source_affine'],recipe)
            require(r['label_influences_image'] is False and r['crop']=='none','Target-dependent transform')
            payload+=math.prod(shape)*5
    require(payload<=PAYLOAD_CAP,'Cache payload cap')
    require(len(canonical(binding))<=OVERHEAD_CAP//2,'Binding metadata cap')
    return payload


def arrays(image,label,shape):
    def plain(t):return t.as_tensor() if hasattr(t,'as_tensor') else torch.as_tensor(t)
    x=plain(image);y=plain(label)
    require(x.device.type=='cpu' and y.device.type=='cpu' and x.dtype==torch.float32 and list(x.shape)==[1,*shape] and y.shape==x.shape,'Array dtype/grid differs')
    require(torch.isfinite(x).all().item() and x.min()>=0 and x.max()<=1,'Invalid normalized image')
    require(torch.all((y==0)|(y==1)).item() and y.any().item(),'Invalid nonempty binary target')
    return x.detach().contiguous().numpy(),y.detach().to(torch.uint8).contiguous().numpy()


def safe_directory(path):
    p=Path(path);require(p.is_absolute() and p.exists() and p.is_dir() and p.resolve()==p,'Unsafe cache directory')
    return p


def read_member(path,name,ref):
    require(Path(name).name==name and name not in ('.','..'),'Unsafe member name')
    p=path/name;require(not p.is_symlink() and p.is_file() and p.stat().st_size==ref['bytes'],'Missing/changed cache member')
    require(0<ref['bytes']<=OVERHEAD_CAP+16_000_000*4,'Member byte cap')
    raw=p.read_bytes();require(digest(raw)==ref['sha256'],'Cache member hash differs');return raw


def publish(path,datasets,binding,pin,*,guard=lambda:None):
    """Path must already be an authorized empty directory; caller enforces registered roots."""
    expected=checked_binding(binding,pin);path=safe_directory(path)
    require(not any(path.iterdir()),'Cache destination is not empty')
    require(set(datasets)==set(ROLES),'Both datasets required')
    # Reject descriptor/recipe drift before the first source load.
    for role in ROLES:
        ds=datasets[role];entries=binding['roles'][role]
        require(len(ds)==len(entries) and ds.recipe==binding['recipe'],'Dataset recipe/count differs')
        require([ds.descriptor(i) for i in range(len(ds))]==[e['descriptor'] for e in entries],'Dataset membership differs')
    manifest={'schema_version':'twomm-cache-1','binding_sha256':pin,'payload_bytes':expected,'entries':[]}
    written=0
    def write(name,raw):
        nonlocal written
        guard();require(shutil.disk_usage(path).free-len(raw)>=FREE_FLOOR,'Internal free-space floor')
        require(written+len(raw)<=expected+OVERHEAD_CAP,'Cache serialization cap')
        with (path/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        written+=len(raw)
        return dict(bytes=len(raw),sha256=digest(raw))
    for role in ROLES:
        for i,e in enumerate(binding['roles'][role]):
            guard();item=datasets[role].load(i,operation=role)
            require(item['provenance']['descriptor']==e['descriptor'] and item['transform_record']==e['transform_record'],'Loaded provenance/transform differs')
            x,y=arrays(item['image'],item['label'],e['transform_record']['processed_shape'])
            files={}
            for kind,a in [('image',x),('label',y)]:
                stream=BytesIO();np.save(stream,a,allow_pickle=False);name=f'{role}-{i:04d}-{kind}.npy';files[kind]=dict(name=name,**write(name,stream.getvalue()))
            manifest['entries'].append(dict(role=role,index=i,study_id=e['descriptor']['study_id'],files=files))
            del item,x,y
    manifest['binding']=binding
    # Verify all serialized arrays before making completion visible.
    for entry in manifest['entries']: _load_entry(path,entry,binding)
    guard();raw=canonical(manifest);write('complete.json',raw)
    return digest(raw)


def _load_entry(path,entry,binding):
    role=entry['role'];i=entry['index'];e=binding['roles'][role][i];values={}
    require(entry['study_id']==e['descriptor']['study_id'],'Entry identity differs')
    require(set(entry['files'])=={'image','label'},'Array inventory differs')
    for kind,dtype in [('image',np.dtype('float32')),('label',np.dtype('uint8'))]:
        ref=entry['files'][kind];require(ref['name']==f'{role}-{i:04d}-{kind}.npy','Array name differs')
        raw=read_member(path,ref['name'],ref);a=np.load(BytesIO(raw),allow_pickle=False)
        require(a.dtype==dtype and list(a.shape)==[1,*e['transform_record']['processed_shape']],'Serialized dtype/grid differs')
        values[kind]=torch.from_numpy(a.copy())
    arrays(values['image'],values['label'],e['transform_record']['processed_shape'])
    return dict(**values,study_id=entry['study_id'],operation=role,transform_record=deepcopy(e['transform_record']),descriptor=deepcopy(e['descriptor']))


class DiskRoleCache:
    def __init__(self,path,receipt_pin,binding,binding_pin):
        self.path=safe_directory(path);expected=checked_binding(binding,binding_pin)
        p=self.path/'complete.json';require(p.is_file() and not p.is_symlink() and p.stat().st_size<=OVERHEAD_CAP,'Cache incomplete/metadata cap')
        raw=p.read_bytes();require(digest(raw)==receipt_pin,'Completion pin differs')
        m=json.loads(raw);require(set(m)=={'schema_version','binding_sha256','payload_bytes','entries','binding'},'Completion fields differ')
        require(m['schema_version']=='twomm-cache-1' and m['binding']==binding and m['binding_sha256']==binding_pin and m['payload_bytes']==expected,'Cache binding differs')
        order=[(role,i,e['descriptor']['study_id']) for role in ROLES for i,e in enumerate(binding['roles'][role])]
        require([(e['role'],e['index'],e['study_id']) for e in m['entries']]==order,'Cache membership/order differs')
        names={'complete.json'};total=p.stat().st_size
        for e in m['entries']:
            _load_entry(self.path,e,binding)
            for ref in e['files'].values():names.add(ref['name']);total+=ref['bytes']
        require({p.name for p in self.path.iterdir()}==names and total<=expected+OVERHEAD_CAP,'Unexpected files/cache byte cap')
        self._manifest=deepcopy(m);self._pin=receipt_pin

    def members(self,role):
        require(role in ROLES,'Explicit operation required')
        require(digest(canonical(self._manifest))==self._pin,'In-memory cache binding changed')
        return [e['study_id'] for e in self._manifest['entries'] if e['role']==role]

    def get(self,role,index):
        ids=self.members(role);require(type(index)==int and 0<=index<len(ids),'Invalid member index')
        e=next(e for e in self._manifest['entries'] if e['role']==role and e['index']==index)
        return _load_entry(self.path,e,self._manifest['binding'])
