"""Provided-pancreas128 native-detail inputs with explicit relocated identities.

Reuses lossless qualified target cache and geometry primitives. No1.5mm resample,
no z-score change, no lesion-based inference box. Roles and schedule are explicit.
"""
import hashlib,json
from pathlib import Path
import numpy as np
import nibabel as nib
from src.data.segmenter_fast_varied_v1 import normalize_region
from src.data.segmenter_native_windows_v1 import geometry,orient,tiles
from src.data.segmenter_pancreas_region_v1 import crop_case
from src.data.segmenter_physical_windows_v1 import sample_window,physical_geometry,PhysicalReconstructor
from src.data.segmenter_content_v1 import target_content
from src.training.segmenter_augmentation_v1 import augment
from src.training.pants_native_evaluation import native_metrics


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def stat(p):
    s=Path(p).stat()
    return dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)


def select_origin(entry,metadata,step,seed=42):
    shape=metadata['record']['shape'];kind=entry['kind']
    if kind=='coverage':return tuple(entry['origin']),{'kind':kind}
    key=hashlib.sha256(f'stunet128-v1:{seed}:{step}:{entry["case_id"]}'.encode()).digest()
    rng=np.random.Generator(np.random.PCG64(int.from_bytes(key[:8],'little')))
    if kind=='context':return tuple(int(rng.integers(max(0,n-128)+1)) for n in shape),{'kind':kind}
    if kind!='component_jitter':raise ValueError('Unknown view')
    parts=metadata['parts'];part=parts[int(rng.integers(len(parts)))];fits=all(h-l<=128 for l,h in zip(part['low'],part['high']))
    low=part['low'] if fits else part['anchor'];high=part['high'] if fits else [x+1 for x in part['anchor']]
    origins=[]
    for n,l,h in zip(shape,low,high):
        a,b=max(0,h-128),min(l,max(0,n-128))
        if a>b:raise ValueError('No component-retaining window')
        origins.append(int(rng.integers(a,b+1)))
    return tuple(origins),dict(kind=kind,anchor=part['anchor'],whole_component_fits=fits)


class Inputs:
    def __init__(self,configuration,*,qualification=False):
        self.config=json.loads(Path(configuration).read_text());self.identity=sha(configuration)
        c=self.config
        if c['qualification_only'] and not qualification:raise ValueError('Nonpromotable inputs')
        if sha(c['plan'])!=c['plan_sha256']:raise ValueError('Plan changed')
        self.plan=json.loads(Path(c['plan']).read_text());self.cache=Path(c['target_cache'])
        if sha(self.cache/'manifest.json')!=self.plan['cache_manifest_sha256']:raise ValueError('Cache manifest changed')
        self.sources=c['sources'];self.train=set(self.plan['members']);self.dev=set(c['development'])
        if len(self.train)!=1333 or len(self.dev)!=70 or self.train&self.dev or set(self.sources)!=self.train|self.dev:
            raise ValueError('Exact1333/70 roles required')
        if len(self.plan['schedule'])!=12000:raise ValueError('Schedule changed')

    def check_file(self,name,kind):
        entry=self.sources[name][kind]
        if stat(entry['path'])!=entry['stat']:raise ValueError('Source observation changed: '+name+':'+kind)
        return Path(entry['path'])

    def training(self,step):
        if type(step)!=int or not 0<=step<12000:raise ValueError('Invalid training step')
        entry=self.plan['schedule'][step];name=entry['case_id']
        if name not in self.train:raise ValueError('Protected optimizer role')
        expected=self.plan['members'][name];mp=self.cache/(name+'.json');ap=self.cache/(name+'.npz')
        if sha(mp)!=expected['cache']['metadata_sha256'] or sha(ap)!=expected['cache']['target_sha256']:raise ValueError('Target cache changed')
        m=json.loads(mp.read_text())
        if m['source_sha256']['ct']!=self.sources[name]['ct']['sha256']:raise ValueError('CT/target provenance mismatch')
        with np.load(ap,allow_pickle=False) as f:
            if f.files!=['target']:raise ValueError('Unexpected target payload')
            target=f['target']
        ct=nib.load(self.check_file(name,'ct'));parent=m['parent_geometry']
        if ct.shape!=tuple(parent['source_shape']) or not np.allclose(ct.affine,parent['source_affine'],atol=1e-5,rtol=0):raise ValueError('CT geometry changed')
        if np.prod(ct.shape,dtype=np.int64)>256000000:raise ValueError('Source size cap')
        image=normalize_region(ct.get_fdata(dtype=np.float32,caching='unchanged'),parent,m['region_low'],m['region_high'])
        origin,view=select_origin(entry,m,step)
        x,transform=sample_window(image,m['record'],origin,order=1,window=128)
        y,_=sample_window(target,m['record'],origin,order=0,window=128)
        if view['kind']=='component_jitter':
            anchor=tuple(a-o for a,o in zip(view['anchor'],origin))
            if any(not 0<=v<128 for v in anchor) or y[anchor]!=(2 if m['positive'] else 1):raise ValueError('Focused target lost')
        x,y,augmentation=augment(x[None],y,transform,seed=42,update=step+1,case_id=name)
        return np.ascontiguousarray(x),np.ascontiguousarray(y),dict(case_id=name,step=step,origin=list(origin),view=view,
            augmentation=augmentation,lesion_voxels=int((y==2).sum()),target_sha256=hashlib.sha256(y.tobytes()).hexdigest(),
            image_sha256=hashlib.sha256(x.tobytes()).hexdigest())

    def development(self,name):
        if name not in self.dev:raise ValueError('Development-only reconstruction')
        objects={kind:nib.load(self.check_file(name,kind)) for kind in ('ct','pancreas','lesion')}
        ct=objects['ct'];source=self.sources[name]
        if ct.shape!=tuple(source['native_shape']) or not np.allclose(ct.affine,source['native_affine'],atol=1e-5,rtol=0):raise ValueError('Development geometry changed')
        if np.prod(ct.shape,dtype=np.int64)>256000000:raise ValueError('Source voxel cap')
        parent=geometry(ct.shape,ct.affine);masks={}
        for kind in ('pancreas','lesion'):
            obj=objects[kind]
            if obj.shape!=ct.shape or not np.allclose(obj.affine,ct.affine,atol=1e-5,rtol=0):raise ValueError('Mask alignment')
            masks[kind],_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
        if not masks['pancreas'].any():raise ValueError('Empty pancreas')
        target=orient(masks['pancreas'],parent).astype(np.uint8);target[orient(masks['lesion'],parent)!=0]=2
        case=crop_case(dict(name=name,target=target,geometry=parent,positive=bool(masks['lesion'].any()),original_pancreas=masks['pancreas']))
        if int((case['target']==2).sum())!=int(masks['lesion'].sum()):raise ValueError('Lesion field clipped')
        if np.count_nonzero(case['target'])!=np.count_nonzero(target):raise ValueError('Annotated pancreas field clipped')
        case['image']=normalize_region(ct.get_fdata(dtype=np.float32,caching='unchanged'),parent,case['region_low'],case['region_high'])
        case.update(original_pancreas=masks['pancreas'],original_lesion=masks['lesion'])
        return case


def predict(model,case,*,progress=lambda **kw:None):
    import torch
    record=physical_geometry(case['geometry']);windows=tiles(record['shape'],window=128,stride=64)
    recon=PhysicalReconstructor(record,window=128);was_training=model.training;deep=model.decoder.deep_supervision
    model.eval();model.decoder.deep_supervision=False
    try:
        with torch.no_grad():
            for index,origin in enumerate(windows):
                image,_=sample_window(case['image'],record,origin,order=1,window=128)
                output=model(torch.from_numpy(image[None,None]).to('cuda'))
                probabilities=output.float().softmax(1)[0].cpu().numpy()
                recon.add(origin,probabilities);progress(tile=index+1,total=len(windows))
                del output,probabilities
        local=recon.finish(windows).argmax(0).astype(np.uint8);parent=case['parent_geometry']
        codes=np.zeros(parent['shape'],np.uint8);slices=tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))
        codes[slices]=local;native=orient(codes,parent,inverse=True)
        return dict(case_id=case['name'],tiles=len(windows),gaps=0,scope='provided_pancreas_region_exploratory',
                    metrics=native_metrics(native,case['original_pancreas'],case['original_lesion'],np.asarray(parent['source_affine'])))
    finally:
        model.decoder.deep_supervision=deep;model.train(was_training)
