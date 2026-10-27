import json
import torch
from test_distillation_integration_v1 import Provider, store, isolated_cpu
from test_kd_evidence_executor_v1 import evaluate
from src.data.manifest_records import canonical,digest
from src.training.segmenter_full_session_v1 import Session,DICE_FOCAL
from src.training.segmenter_errata_kd_session_v1 import OnDemandStudent,ErrataKDSession
from src.training.segmenter_distillation_v1 import DistillationConfig
from src.training.kd_executor_qualification_v1 import exercise
from scripts.diagnostics.mac_kd_synthetic import compare


def test_all_four_stages_preserve_horizon_and_restore_next_update(tmp_path):
    p=Provider();p.control['validation']=['positive','empty'];p.pin=digest(canonical(p.control))
    target_root=tmp_path/'targets';target_root.mkdir();targets=store(target_root,p)
    config=dict(max_steps=24000,lr_horizon_steps=24000,tensor_shape=[16]*3,seed=42,
                learning_rate=1e-4,weight_decay=1e-5,warmup_steps=500,
                lr_schedule='warmup_cosine',loss_id=DICE_FOCAL)
    def student():return OnDemandStudent(Session(config,p.control,device='cpu',initialization={'kind':'scratch'}))
    def kd(weight):return ErrataKDSession(student(),teacher_identity={'weights':{'sha256':'a'*64}},
        loss_config=DistillationConfig(max_weight=weight),target_manifest_sha256=targets.pin)
    request=dict(backup=str(tmp_path/'backup'),development=dict(positive='positive',empty='empty'))
    for stage in ('reference','zero','producer','cold'):
        (tmp_path/stage).mkdir()
        exercise(tmp_path,stage,request,inputs=p,targets=targets,student=student,kd=kd,
                 tick=lambda:None,compare=compare,evaluate=evaluate,backup_admission=lambda size:None)
        result=json.loads((tmp_path/stage/'result.json').read_text())
        assert result['success'] and result['scientific_updates']==0
        assert result['engineering_updates']==(1 if stage=='cold' else 4)
    saved=torch.load(tmp_path/'backup/000003-last.pt',weights_only=True,map_location='cpu')
    assert saved['session']['student']['identity']['raw']['config']['max_steps']==24000
    assert len(json.loads((tmp_path/'producer/updates.json').read_text()))==4
