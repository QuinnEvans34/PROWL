"""Inherit qualified corrected inputs; change only sampling addresses."""
import copy
from src.data.stunet_continuation_inputs_20261108 import *
from src.data.stunet_continuation_inputs_20261108 import Inputs as PreviousInputs
from src.data.stunet_longer_schedule_20261110 import new_schedule
class Inputs(PreviousInputs):
    def __init__(self,configuration,*,qualification=False):
        c=json.loads(Path(configuration).read_text())
        if sha(c['previous_inputs'])!=c['previous_inputs_sha256']:raise ValueError('Previous inputs changed')
        super().__init__(c['previous_inputs'])
        if c['plan']!=self.config['plan'] or sha(c['plan'])!=c['plan_sha256']:raise ValueError('Plan binding changed')
        self.plan=copy.deepcopy(self.plan);self.plan['schedule']=new_schedule(self.plan['members'])
        self.identity=sha(configuration)
    def training(self,step):
        if type(step)!=int or not 24000<=step<36000:raise ValueError('Invalid training step')
        entry=self.plan['schedule'][step-24000];name=entry['case_id']
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

