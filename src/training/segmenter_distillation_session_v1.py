"""Additive KD integration with unchanged raw Session and varied-view provider.

No scientific launcher here. Actual data/CUDA/cold qualification is mandatory.
"""
from copy import deepcopy
from dataclasses import asdict
import torch

from src.data.manifest_records import canonical,digest
from src.data.segmenter_physical_windows_v1 import physical_geometry
from src.data.segmenter_teacher_targets_v1 import apply_spatial_trace
from src.training.segmenter_full_session_v1 import Session,objective,learning_rate_factor
from src.training import segmenter_session_v1 as numerical
from src.training.segmenter_fast_varied_session_v1 import FastVariedSession,member_at
from src.training.segmenter_pancreas_region_session_v1 import Adapter
from src.training.segmenter_distillation_v1 import DistillationConfig,add_teacher_guidance,POLICY


class DistillationSession:
    def __init__(self,student,*,teacher_identity,loss_config,target_manifest_sha256):
        if not isinstance(student,FastVariedSession) or not isinstance(loss_config,DistillationConfig):
            raise ValueError('Versioned student and KD recipe required')
        if student.step!=0:raise ValueError('Fresh KD session required; use checked restore')
        self.student=student;self.loss_config=loss_config
        self.identity=dict(version='distillation-region-session-1',student=deepcopy(student.identity),
            teacher=deepcopy(teacher_identity),loss=dict(policy=POLICY,**asdict(loss_config)),
            target_manifest_sha256=target_manifest_sha256)
        self.identity_pin=digest(canonical(self.identity))

    def __getattr__(self,key):return getattr(self.student,key)

    def check(self):
        if digest(canonical(self.identity))!=self.identity_pin or self.identity['student']!=self.student.identity:
            raise ValueError('KD identity changed')
        if self.identity['loss']!=dict(policy=POLICY,**asdict(self.loss_config)):raise ValueError('KD recipe changed')
        self.student.check();self.raw._clean()

    def update(self,provider,targets=None):
        self.check()
        weight=self.loss_config.weight(self.step+1)
        if weight==0:
            # Delegate the unchanged production update, without any teacher reads.
            row=self.student.update(provider)
            return dict(row,supervised_loss=row['loss'],kd_loss=0.,kd_weight=0.,teacher_accessed=False)
        if targets is None or targets.pin!=self.identity['target_manifest_sha256']:
            raise ValueError('Bound teacher targets required')
        if targets.control!=self.control:raise ValueError('Teacher/student cohort differs')
        if targets.common['teacher_sha256']!=self.identity['teacher']['weights']['sha256']:
            raise ValueError('Target teacher differs from checkpoint identity')
        s=self.raw;step=s.step;name=s.next_member();request=None
        if step+1<s.config['max_steps']:
            following=member_at(s.control['train'],step+1,s.config['seed'])
            visit=self.focused[following]+int(following==name and step%4!=3)
            request=(following,step+1,visit,s.config['seed'])
        provider.plan_next(request)
        adapter=Adapter(provider,self.student)
        batch,x,y=s._batch(adapter,name,'train','optimizer')
        _,small=provider.cache_member(name)
        record=physical_geometry(small['geometry']);trace=adapter.trace
        if trace['window']['region_low']!=small['region_low'] or trace['window']['region_high']!=small['region_high']:
            raise ValueError('Teacher region differs from actual student input')
        q,valid,provenance=targets.window(name,small,record,trace['window']['origin'],window=s.config['tensor_shape'][0])
        q,valid=apply_spatial_trace(q,valid,trace['augmentation'])
        c=s.config
        for group in s.optimizer.param_groups:group['lr']=c['learning_rate']*learning_rate_factor(c,step)
        s.dirty=True
        with s.rng_scope():
            s.model.train();s.optimizer.zero_grad(set_to_none=True)
            logits=s.model(x[None].to(s.device));target=y[None].to(s.device)
            supervised=objective(logits,target,c)
            total,metrics=add_teacher_guidance(supervised,logits,target,
                torch.as_tensor(q[None],device=s.device),torch.as_tensor(valid[None],device=s.device),
                config=self.loss_config,one_based_update=step+1)
            if not torch.isfinite(total).item():raise ValueError('Nonfinite KD total')
            total.backward()
            if not all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in s.model.parameters()):
                raise ValueError('Missing/nonfinite KD gradient')
            s.optimizer.step()
            if not numerical.finite(s.model.state_dict()) or not numerical.finite(s.optimizer.state_dict()):
                raise ValueError('Nonfinite KD state')
        s.step+=1;s.exposure[name]+=1
        if step%4!=3:self.focused[name]+=1
        s.dirty=False;self.check()
        return dict(step=s.step,member_id=name,loss=float(total.detach().cpu()),
            supervised_loss=float(supervised.detach().cpu()),kd_loss=float(metrics['kd'].cpu()),kd_weight=weight,
            eligible_voxels=metrics['eligible_voxels'],conflict_or_tie_voxels=metrics['conflict_or_tie_voxels'],
            valid_voxels=metrics['valid_voxels'],teacher_accessed=True,teacher_target=provenance,
            learning_rate=s.optimizer.param_groups[0]['lr'],batch_sha256=batch.hashes(),input_view=trace)

    def state(self):
        self.check()
        return dict(version=1,identity=deepcopy(self.identity),identity_sha256=self.identity_pin,
            student=self.student.state())

    @classmethod
    def restore(cls,state,expected_identity):
        if (state['version']!=1 or state['identity']!=expected_identity or
            state['identity_sha256']!=digest(canonical(expected_identity))):raise ValueError('KD checkpoint identity')
        # Restore raw state and sampler via the existing tested state validator.
        student=FastVariedSession.restore(state['student'],expected_identity['student'])
        result=object.__new__(cls);result.student=student
        recipe={k:v for k,v in expected_identity['loss'].items() if k!='policy'}
        result.loss_config=DistillationConfig(**recipe)
        result.identity=deepcopy(expected_identity);result.identity_pin=state['identity_sha256']
        result.check();return result


class BoundDistillationSession:
    """Executor facade keeps the existing native evaluator entirely teacher-free."""
    def __init__(self,session,targets):self.session,self.targets=session,targets
    def __getattr__(self,key):return getattr(self.session,key)
    def update(self,provider):return self.session.update(provider,self.targets)


def live_metrics(row):
    """Additional journal-derived metrics for MLflow; does not create or mutate runs."""
    if row.get('event')!='update' or not (row['step']==1 or row['step']%25==0):return {}
    keys=('supervised_loss','kd_loss','kd_weight','eligible_voxels','conflict_or_tie_voxels','valid_voxels')
    return {'train/'+key:float(row[key]) for key in keys if key in row}
