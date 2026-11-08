"""Increasing the resource envelope must fail before checkpoint/data access."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.diagnostics import run_stunet_confidence_mac_20261108_v3 as screen


class AuthorityTests(unittest.TestCase):
    def test_missing_approval_cannot_read_weights(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(screen,'BASE',Path(temp)), \
                patch.object(screen,'safety'),patch.object(screen,'sha') as hash_file:
            with self.assertRaises(FileNotFoundError):screen.prepare()
            hash_file.assert_not_called()

    def test_unapproved_or_different_cap_cannot_read_weights(self):
        for approval in ({'approved':False,'mps_bytes':8*1024**3},
                         {'approved':True,'mps_bytes':12*1024**3}):
            with self.subTest(approval=approval),tempfile.TemporaryDirectory() as temp, \
                    patch.object(screen,'BASE',Path(temp)),patch.object(screen,'safety'), \
                    patch.object(screen,'sha') as hash_file:
                (Path(temp)/'user-mps8-approval.json').write_text(json.dumps(approval))
                with self.assertRaisesRegex(ValueError,'Explicit8GiB'):screen.prepare()
                hash_file.assert_not_called()

    def test_approval_alone_cannot_skip_real_qualification(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(screen,'BASE',Path(temp)), \
                patch.object(screen,'safety'),patch.object(screen,'sha') as hash_file:
            (Path(temp)/'user-mps8-approval.json').write_text(json.dumps({'approved':True,'mps_bytes':8*1024**3}))
            with self.assertRaises(FileNotFoundError):screen.prepare()
            hash_file.assert_not_called()

    def test_result_cannot_hide_failed_or_unreaped_qualification(self):
        for resources in ({'success':False,'workers_reaped':True,'exit_code':1},
                          {'success':True,'workers_reaped':False,'exit_code':0}):
            with self.subTest(resources=resources),tempfile.TemporaryDirectory() as temp, \
                    patch.object(screen,'BASE',Path(temp)),patch.object(screen,'safety'), \
                    patch.object(screen,'sha') as hash_file:
                base=Path(temp)
                (base/'user-mps8-approval.json').write_text(json.dumps({'approved':True,'mps_bytes':8*1024**3}))
                q=base/'cache-release-qualification-02';q.mkdir()
                (q/'result.json').write_text(json.dumps({'status':'PASS_EXACT_OUTPUTS_CACHE_RELEASE'}))
                (q/'resources.json').write_text(json.dumps(resources))
                with self.assertRaisesRegex(ValueError,'reaped'):screen.prepare()
                hash_file.assert_not_called()


if __name__=='__main__':unittest.main()
