import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import torch
from src.training.stunet_session_20261106 import Session,compare
from scripts.training.train_stunet_transfer_20261106 import backup,summary
from scripts.training.supervise_stunet_transfer_20261106 import verify,sha,Tracking


class LaunchTests(unittest.TestCase):
    def test_actual_adam_full_state_cold_replay_cpu(self):
        class Model(torch.nn.Module):
            def __init__(self):
                super().__init__();self.conv=torch.nn.Conv3d(1,3,1);self.decoder=SimpleNamespace(deep_supervision=True)
            def forward(self,x):return [self.conv(x)]*5
        class Provider:
            identity='fixed'
            def training(self,step):return np.ones((1,4,4,4),np.float32),np.ones((4,4,4),np.uint8),dict(case_id='train',step=step)
        identity=dict(input_sha256='fixed',train=['train'])
        a=Session(Model(),identity,device='cpu');provider=Provider()
        for _ in range(4):a.update(provider)
        state=a.state();expected=a.update(provider);expected_state=a.state()
        b=Session(Model(),identity,device='cpu');b.restore(state);compare(state,b.state())
        actual=b.update(provider);self.assertEqual(expected,actual);compare(expected_state,b.state())
        altered=dict(state,identity={'input_sha256':'other'})
        with self.assertRaises(ValueError):b.restore(altered)

    def test_independent_backup_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_bytes(b'checkpoint');q=Path(d)/'backup'
            result=backup(p,q);self.assertEqual(result['sha256'],sha(q))
            with self.assertRaises(FileExistsError):backup(p,q)

    def test_scientific_gate_rejects_unreaped_and_changed_pin(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'result';p.write_text(json.dumps({'status':'PASS'}))
            resource=Path(d)/'resources';resource.write_text(json.dumps({'success':True,'workers_reaped':False}))
            r=dict(pins={str(p):sha(p)},seconds=216000,rss_bytes=12*1024**3,cuda_bytes=6*1024**3,approval='Approve a 60-hour cap',
                producer_resources=str(resource),cold_resources=str(resource),producer_result=str(p),cold_result=str(p))
            with self.assertRaises(ValueError):verify(r,'science')
            resource.write_text(json.dumps({'success':True,'workers_reaped':True}));verify(r,'science')
            p.write_text('{}')
            with self.assertRaises(ValueError):verify(r,'science')

    def test_tracking_reads_only_complete_lines_without_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'journal';row=dict(event='update',step=1,utc_ms=1,loss=.5,learning_rate=.01)
            p.write_text(json.dumps(row)+'\n'+json.dumps(dict(row,step=2)))
            t=Tracking.__new__(Tracking);t.offset=0;t.losses=0;t.id='test';t.client=SimpleNamespace(log_batch=lambda *a,**k:None)
            t.sync(p);self.assertEqual(t.losses,1);t.sync(p);self.assertEqual(t.losses,1)
            with p.open('a') as f:f.write('\n')
            t.sync(p);self.assertEqual(t.losses,2)


if __name__=='__main__':unittest.main()
