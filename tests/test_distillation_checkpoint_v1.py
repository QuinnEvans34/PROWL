from collections import OrderedDict
import pytest
import torch
from src.training.teacher_checkpoint_v1 import read_legacy_release,tensor_state,InertModuleRecord


def test_legacy_module_is_inert_and_tensors_are_exact(tmp_path):
    model=torch.nn.Sequential(torch.nn.Conv3d(1,3,1),torch.nn.ReLU(),torch.nn.Identity())
    path=tmp_path/'legacy.pt';torch.save({'model_state_dict':model},path)
    value,names=read_legacy_release(path)
    assert type(value['model_state_dict']) is InertModuleRecord
    assert 'torch.nn.modules.conv.Conv3d' in names
    result=tensor_state(value['model_state_dict'])
    assert set(result)==set(model.state_dict())
    assert all(torch.equal(result[k],v) for k,v in model.state_dict().items())
    assert not hasattr(value['model_state_dict'],'forward')


def test_unreviewed_module_class_is_not_dynamically_allowed(tmp_path):
    path=tmp_path/'other.pt';torch.save({'model_state_dict':torch.nn.Embedding(2,3)},path)
    with pytest.raises(ValueError,match='Unreviewed'):read_legacy_release(path)


def test_direct_state_is_supported_and_cycles_are_rejected():
    state=OrderedDict(a=torch.ones(1));assert torch.equal(tensor_state(state)['a'],state['a'])
    item=InertModuleRecord();item._parameters={};item._buffers={};item._modules={'self':item}
    with pytest.raises(ValueError,match='cyclic'):tensor_state(item)


def test_custom_hooks_cannot_execute():
    item=InertModuleRecord();item._state_dict_hooks={'x':object()}
    with pytest.raises(ValueError,match='hooks'):tensor_state(item)
