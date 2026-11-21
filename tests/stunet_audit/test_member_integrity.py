import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.stunet_audit.extract_accessible_reference_ct import copy_member

class MemberIntegrityTests(unittest.TestCase):
    def test_bad_crc_never_returns_an_admitted_digest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'synthetic.zip';data=b'synthetic-CT-bytes-only'*100
            with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_STORED) as z:z.writestr('ct.nii.gz',data)
            raw=bytearray(path.read_bytes());offset=raw.index(data);raw[offset]^=1;path.write_bytes(raw)
            partial=root/'ct.nii.gz.partial'
            with zipfile.ZipFile(path) as z:
                with self.assertRaises(zipfile.BadZipFile):copy_member(z,z.getinfo('ct.nii.gz'),partial)
            self.assertTrue(partial.exists())
            self.assertFalse((root/'ct.nii.gz').exists())

    def test_good_crc_has_bound_complete_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'synthetic.zip';data=b'synthetic-only'*100
            with zipfile.ZipFile(path,'w') as z:z.writestr('ct.nii.gz',data)
            partial=root/'ct.nii.gz.partial'
            with zipfile.ZipFile(path) as z:digest=copy_member(z,z.getinfo('ct.nii.gz'),partial)
            self.assertEqual(digest,hashlib.sha256(data).hexdigest())
            self.assertEqual(partial.read_bytes(),data)

if __name__=='__main__':unittest.main()
