"""Offline KD with explicit on-demand throughput identity and checked recovery."""
from copy import deepcopy
from dataclasses import asdict
from src.data.manifest_records import canonical,digest
from src.data.pants_errata_kd_inputs_v1 import THROUGHPUT
from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
from src.training.segmenter_distillation_session_v1 import DistillationSession
from src.training.segmenter_distillation_v1 import DistillationConfig,POLICY

class OnDemandStudent(FastVariedSession):
    def __init__(self,raw):
        super().__init__(raw)
        self.identity['version']='errata-on-demand-student-1'
        self.identity['throughput']=deepcopy(THROUGHPUT)
        self.identity_pin=digest(canonical(self.identity))
    def check(self):
        super().check()
        if self.identity['throughput']!=THROUGHPUT:raise ValueError('On-demand policy mismatch')

class ErrataKDSession(DistillationSession):
    def __init__(self,student,**kwargs):
        if not isinstance(student,OnDemandStudent):raise ValueError('On-demand student required')
        super().__init__(student,**kwargs)
    @classmethod
    def restore(cls,state,expected_identity):
        if state['version']!=1 or state['identity']!=expected_identity or state['identity_sha256']!=digest(canonical(expected_identity)):raise ValueError('KD checkpoint identity')
        student=OnDemandStudent.restore(state['student'],expected_identity['student'])
        result=object.__new__(cls);result.student=student
        result.loss_config=DistillationConfig(**{k:v for k,v in expected_identity['loss'].items() if k!='policy'})
        result.identity=deepcopy(expected_identity);result.identity_pin=state['identity_sha256'];result.check();return result
