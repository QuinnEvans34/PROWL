import copy
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
from scripts.diagnostics.run_universal_screen_20261105 import validate_permit, read_request


class PermitTests(unittest.TestCase):
    def setUp(self):
        self.p={'schema':'prowl.post-kd-trial-permit.v1','action':'one_fresh_exploratory_universal_swin_trial',
                'trial_request_sha256':'a'*64,'specification_sha256':'b'*64,
                'kd_execution_closeout_verified':True,'automatic_retry':False,
                'authorizes_additional_experiments':False,'maximum_dispatches':1,
                'kd_ready_sha256':'c'*64,'kd_report_sha256':'d'*64}
    def test_exact(self):validate_permit(self.p,'a'*64,'b'*64)
    def test_each_gate_required(self):
        for key in self.p:
            p=copy.deepcopy(self.p);del p[key]
            with self.subTest(key=key),self.assertRaises(ValueError):validate_permit(p,'a'*64,'b'*64)
    def test_wrong_request(self):
        with self.assertRaises(ValueError):validate_permit(self.p,'e'*64,'b'*64)
    def test_wrong_spec(self):
        with self.assertRaises(ValueError):validate_permit(self.p,'a'*64,'e'*64)
    def test_no_retry(self):
        self.p['automatic_retry']=True
        with self.assertRaises(ValueError):validate_permit(self.p,'a'*64,'b'*64)
    def test_request_pin_and_file_observation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'dependency.py';source.write_bytes(b'original')
            st=source.stat();r={'pins':{str(source):hashlib.sha256(b'original').hexdigest()},
                'pin_observations':{str(source):[st.st_size,st.st_mtime_ns]},'environment_dependency_paths':[str(source)],
                'cases':['PanTS_00002028','PanTS_00001347','PanTS_00002514','PanTS_00008743'],'training_admission':'NOT_ADMITTED'}
            request=root/'request.json';request.write_text(json.dumps(r));pin=hashlib.sha256(request.read_bytes()).hexdigest()
            with patch('scripts.diagnostics.run_universal_screen_20261105.PREP',root):
                self.assertEqual(read_request(pin,full=True),r)
                source.write_bytes(b'changed')
                with self.assertRaises(ValueError):read_request(pin)


if __name__=='__main__':unittest.main()
