import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from scripts.training.supervise_stunet_transfer_20261106_v2 import input_pin,Tracking
from scripts.training.supervise_stunet_transfer_20261106 import sha


class TrackingCorrectionTests(unittest.TestCase):
    def test_actual_receipt_mixed_slashes(self):
        request=json.loads(Path('E:/PROWL/readiness/stunet-scientific-launch-20261106-a01/ready.json').read_text())
        self.assertEqual(input_pin(request),sha(request['inputs']))
        client=Mock();client.get_experiment_by_name.return_value=SimpleNamespace(experiment_id='1')
        client.create_run.return_value=SimpleNamespace(info=SimpleNamespace(run_id='fake'))
        tracker=Tracking(request,client);self.assertEqual(tracker.id,'fake');self.assertEqual(client.log_param.call_count,7)
        client.log_param.assert_any_call('fake','input_sha256',sha(request['inputs']))

    def test_init_failure_closes_new_record(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text('input');r=dict(inputs=str(p),pins={str(p):sha(p)},title='test',run_id='test')
            client=Mock();client.get_experiment_by_name.return_value=SimpleNamespace(experiment_id='1')
            client.create_run.return_value=SimpleNamespace(info=SimpleNamespace(run_id='fake'));client.log_param.side_effect=RuntimeError('database failure')
            with self.assertRaises(RuntimeError):Tracking(r,client)
            client.set_terminated.assert_called_once_with('fake',status='FAILED')
            r['pins']={};client.reset_mock()
            with self.assertRaises(ValueError):Tracking(r,client)
            client.create_run.assert_not_called()


if __name__=='__main__':unittest.main()
