"""Versioned correction provider; ordinary targets and development path inherited exactly."""
import copy
from src.data.stunet_inputs_20261106 import *
from src.data.stunet_inputs_20261106 import Inputs as ParentInputs
from src.data.stunet_errata_20261108 import EXPECTED,POLICY,new_schedule

class Inputs(ParentInputs):
    def __init__(self,configuration,*,qualification=False):
        c=json.loads(Path(configuration).read_text())
        if sha(c['parent_inputs'])!=c['parent_inputs_sha256']:raise ValueError('Parent inputs changed')
        parent=ParentInputs(c['parent_inputs'])
        if sha(c['plan'])!=c['plan_sha256']:raise ValueError('Corrected plan changed')
        plan=json.loads(Path(c['plan']).read_text())
        if plan['parent_plan_sha256']!=sha(parent.config['plan']):raise ValueError('Wrong parent plan')
        overlay=Path(plan['corrected_cache'])/'overlay.json'
        if sha(overlay)!=plan['overlay_sha256']:raise ValueError('Overlay changed')
        proof=json.loads(overlay.read_text())
        if set(proof['corrected_cases'])!=set(EXPECTED) or not proof['ordinary_bindings_exact']:raise ValueError('Correction proof')
        if set(plan['members'])!=parent.train:raise ValueError('Training membership changed')
        for name,entry in plan['members'].items():
            original=parent.plan['members'][name]
            if name not in EXPECTED:
                if entry!=original:raise ValueError('Ordinary target changed')
            else:
                allowed={'cover','positive','lesion_voxels','cache'}
                if {k:v for k,v in entry.items() if k not in allowed}!={k:v for k,v in original.items() if k not in allowed}:raise ValueError('Unauthorized target geometry/source change')
                if entry['positive'] or entry['lesion_voxels']!=0:raise ValueError('Stale seven positivity')
        if plan['schedule']!=new_schedule(plan['members']):raise ValueError('Schedule mismatch')
        self.__dict__.update(parent.__dict__)
        self.plan=plan;self.corrected=Path(plan['corrected_cache']);self.identity=sha(configuration)
        if Path(plan['original_cache']).resolve()!=self.cache.resolve():raise ValueError('Original cache moved')
        self.config=copy.deepcopy(parent.config)
        self.config['continuation_configuration']=str(configuration)
        self.config['plan']=c['plan']

    def training(self,step):
        if type(step)!=int or not 12000<=step<24000:raise ValueError('Invalid training step')
        entry=self.plan['schedule'][step-12000];name=entry['case_id']
        if name not in self.train:raise ValueError('Protected optimizer role')
        expected=self.plan['members'][name];cache=self.corrected if name in EXPECTED else self.cache
        mp=cache/(name+'.json');ap=cache/(name+'.npz')
        if sha(mp)!=expected['cache']['metadata_sha256'] or sha(ap)!=expected['cache']['target_sha256']:raise ValueError('Target cache changed')
        m=json.loads(mp.read_text())
        if m['source_sha256']['ct']!=self.sources[name]['ct']['sha256']:raise ValueError('CT/target provenance mismatch')
        with np.load(ap,allow_pickle=False) as f:
            if f.files!=['target']:raise ValueError('Unexpected target payload')
            target=f['target']
        if name in EXPECTED and (m.get('annotation_policy')!=POLICY or m['positive'] or (target==2).any()):raise ValueError('Stale corrected target')
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

