import json
from pathlib import Path
import pytest
from scripts.training.supervise_stunet_longer_20261110 import verify,Tracking
from scripts.training.supervise_stunet_transfer_20261106_v2 import input_pin
from src.data.stunet_inputs_20261106 import sha


def request(tmp_path):
    r=dict(parent_checkpoint_sha256='2cb9ff72c66b67f8bcdcb081c5d3f84735a83830f693ad2990fb8139933da92c',pins={},seconds=144000,rss_bytes=12*1024**3,cuda_bytes=6*1024**3,approval='Continue approved same PanTS patients for another 12k')
    for key in ('producer_resources','cold_resources','producer_result','cold_result'):
        p=tmp_path/(key+'.json')
        p.write_text(json.dumps(dict(success=True,workers_reaped=True,status='PASS')))
        r[key]=str(p);r['pins'][str(p)]=sha(p)
    return r


def test_science_requires_successful_bound_qualification(tmp_path):
    r=request(tmp_path);verify(r,'science')
    Path(r['producer_result']).write_text('{"status":"FAIL"}')
    with pytest.raises(ValueError):verify(r,'science')


@pytest.mark.parametrize('key,value',[('seconds',216000),('rss_bytes',20*1024**3),('cuda_bytes',8*1024**3),('approval','')])
def test_caps_and_authority(tmp_path,key,value):
    r=request(tmp_path);r[key]=value
    with pytest.raises(ValueError):verify(r,'science')


def test_unreaped_qualification_cannot_launch(tmp_path):
    r=request(tmp_path);p=Path(r['cold_resources']);p.write_text(json.dumps(dict(success=True,workers_reaped=False)))
    r['pins'][str(p)]=sha(p)
    with pytest.raises(ValueError):verify(r,'science')


def test_pin_lookup_before_mlflow_record(tmp_path):
    p=tmp_path/'inputs.json';p.write_text('{}')
    r=dict(inputs=str(p),pins={str(p):sha(p)})
    assert input_pin(r)==sha(p)
    r['pins']={}
    class Client:
        def create_run(self,*args,**kwargs):raise AssertionError('Should never create a record')
    with pytest.raises(ValueError):Tracking(r,client=Client())
