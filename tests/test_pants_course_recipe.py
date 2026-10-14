from copy import deepcopy
import numpy as np
import pytest
import torch
from monai.losses import DiceFocalLoss
from src.training.segmenter_full_session_v1 import DICE_FOCAL, Session, objective, identity_for, validate_config
from src.training.segmenter_full_executor_v1 import execute
from src.training import segmenter_normalized_loss_v1 as legacy
from src.training.pants_native_evaluation import native_metrics, paired_decision
from test_segmenter_full import Invented, config


@pytest.mark.parametrize('empty', [False, True])
def test_loss_values_and_gradients_match_course_monai(empty):
    torch.manual_seed(7)
    x = torch.randn(1,3,4,4,4, requires_grad=True)
    y = torch.randint(0, 2 if empty else 3, (1,4,4,4))
    z = x.detach().clone().requires_grad_()
    actual = objective(x, y, {'loss_id': DICE_FOCAL})
    expected = DiceFocalLoss(include_background=False,to_onehot_y=True,softmax=True,
                            gamma=2,lambda_dice=1,lambda_focal=1)(z,y[:,None])
    actual.backward(); expected.backward()
    assert torch.equal(actual, expected) and torch.equal(x.grad,z.grad)
    assert torch.isfinite(x.grad).all()


def test_legacy_dispatch_and_identity_unchanged():
    p = Invented(); c = config()
    i = identity_for(c,p.control,'cpu',{'kind':'scratch'})
    assert i['loss'] == legacy.LOSS and 'loss_id' not in i['config']
    x = torch.randn(1,3,4,4,4); y = torch.randint(0,3,(1,4,4,4))
    assert torch.equal(objective(x,y,c),legacy.objective(x,y))
    with pytest.raises(ValueError): validate_config(dict(c,loss_id='typo'))


def test_new_loss_restore_and_milestone_backup_hook(tmp_path):
    torch.set_num_threads(2)
    p=Invented(); c=dict(config(4),loss_id=DICE_FOCAL)
    s=Session(c,p.control,device='cpu',initialization={'kind':'scratch'})
    s.update(p); state=deepcopy(s.state())
    restored=Session.restore(state,s.identity)
    assert s.update(p) == restored.update(p)
    wrong=deepcopy(s.identity);wrong['loss']=legacy.LOSS
    with pytest.raises(ValueError): Session.restore(state,wrong)
    seen=[]
    execute(s,p,tmp_path/'run',validate_every=3,checkpoint_every=1,
            retain_steps=[3,4],checkpoint_hook=lambda path:seen.append(path.name))
    for step in (3,4):
        name=f'step-{step:06d}.pt'
        assert name in seen
        assert torch.load(tmp_path/'run'/name,weights_only=True)['session']['step']==step


def test_native_metrics_misses_outside_crop_and_multiple_lesions():
    truth=np.zeros((8,8,8),np.uint8); truth[1,1,1]=1;truth[6,6,6]=1
    pred=np.zeros_like(truth);pred[1,1,1]=2
    m=native_metrics(pred,np.zeros_like(truth),truth,np.diag([2,2,2,1]))
    assert m['lesion']['dice']==pytest.approx(2/3)
    assert m['reference_components']==2 and m['detected_components']==1
    assert m['target_volume_mm3']==pytest.approx(16)
    m=native_metrics(pred,np.zeros_like(truth),np.zeros_like(truth),np.eye(4))
    assert m['false_alarm_any'] and not m['case_alert_50mm3'] and not m['case_detected']


def test_decision_and_mismatched_cases():
    truth=np.zeros((4,4,4),np.uint8); truth[1,1,1]=1
    blank=np.zeros_like(truth)
    pos=native_metrics(truth*2,blank,truth,np.eye(4))
    neg=native_metrics(blank,blank,blank,np.eye(4))
    a=[dict(case_id='positive',metrics=deepcopy(pos)),dict(case_id='empty',metrics=neg)]
    b=deepcopy(a);a[0]['metrics']['lesion']['dice']=.5
    assert paired_decision(a,b)['status']=='accepted'
    assert paired_decision(b,a)['status']=='rejected'
    b[0]['case_id']='different'
    with pytest.raises(ValueError):paired_decision(a,b)
