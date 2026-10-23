"""Pancreas-assisted window training with checkpointed independent focus counters."""
from copy import deepcopy
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.segmenter_pancreas_region_v1 import POLICY
from src.training.segmenter_augmentation_v1 import augment,augmentation_identity
from src.data import segmenter_full_batch_v1 as boundary
from src.data.segmenter_native_windows_v1 import orient
from src.training.segmenter_full_session_v1 import Session
from src.training.segmenter_physical_windows_session_v1 import predict_native
from src.training.pants_native_evaluation import native_metrics


class Adapter:
    def __init__(self,provider,session):
        self.provider,self.session,self.control=provider,session,provider.control
        self.trace=None

    def get(self,name,*,role,operation):
        if role!='train' or operation!='optimizer':raise ValueError('Optimizer adapter only')
        s=self.session
        image,target,transform,view=self.provider.training_window(name,step=s.step,
            focused_visit=s.focused[name],seed=s.config['seed'])
        image,target,aug=augment(image,target,transform,seed=s.config['seed'],update=s.step+1,case_id=name)
        self.trace=dict(window=view,augmentation=aug)
        return boundary.Batch(boundary._TOKEN,study_id=name,role=role,operation=operation,
            image=image,target=target,control_sha256=self.provider.pin)


class RegionSession:
    def __init__(self,raw):
        self.raw=raw;self.focused={n:0 for n in raw.control['train']}
        self.identity=dict(version='pancreas-region-session-1',raw=deepcopy(raw.identity),
            policy=deepcopy(POLICY),augmentation=augmentation_identity())
        self.identity_pin=digest(canonical(self.identity))

    def __getattr__(self,key):return getattr(self.raw,key)

    def check(self):
        if digest(canonical(self.identity))!=self.identity_pin or self.identity['policy']!=POLICY:raise ValueError('Region identity changed')
        if set(self.focused)!=set(self.exposure) or any(type(v)!=int or v<0 or v>self.exposure[n] for n,v in self.focused.items()):raise ValueError('Focus state invalid')
        if sum(self.focused.values())!=self.step-self.step//4:raise ValueError('Focus totals invalid')

    def update(self,provider):
        self.check();adapter=Adapter(provider,self);step=self.step
        result=self.raw.update(adapter)
        if step%4!=3:self.focused[result['member_id']]+=1
        self.check()
        return dict(result,input_view=adapter.trace)

    def state(self):
        self.check()
        return dict(version=1,identity=deepcopy(self.identity),identity_sha256=self.identity_pin,
            focused=deepcopy(self.focused),raw=self.raw.state())

    @classmethod
    def restore(cls,state,identity):
        if state['version']!=1 or state['identity']!=identity or state['identity_sha256']!=digest(canonical(identity)):raise ValueError('Region checkpoint identity mismatch')
        result=cls(Session.restore(state['raw'],identity['raw']));result.focused=deepcopy(state['focused']);result.check()
        return result


def evaluate(session,provider,name,progress):
    case=provider.load(name,role='validation',operation='evaluator')
    local,reconstruction=predict_native(session.raw,case['image'],case['geometry'],progress=progress)
    parent=case['parent_geometry'];codes=np.zeros(parent['shape'],np.uint8)
    slices=tuple(slice(l,h) for l,h in zip(case['region_low'],case['region_high']))
    if local.shape!=codes[slices].shape:raise ValueError('ROI reconstruction shape')
    codes[slices]=local;codes=orient(codes,parent,inverse=True)
    reconstruction.update(region_low=case['region_low'],region_high=case['region_high'],outside_region='background',
        assistance='provided_pancreas_mask',lesion_guided_region=False)
    return dict(case_id=name,step=session.step,scope='native_provided_pancreas_region_development',
        reconstruction=reconstruction,metrics=native_metrics(codes,case['original_pancreas'],case['original_lesion'],
            np.asarray(parent['source_affine'])))
