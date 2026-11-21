import tempfile
import unittest
from pathlib import Path
import numpy as np
import nibabel as nib
from scripts.stunet_audit.reference_worker import reference_fingerprint
from scripts.stunet_audit.overlap import fingerprint,rank

class ProxyTests(unittest.TestCase):
    def test_proxy_is_appearance_evidence_not_native_equality(self):
        rng=np.random.default_rng(42)
        a=rng.normal(size=(48,48,48)).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'synthetic.nii.gz';n=nib.Nifti1Image(a,np.eye(4));n.header.set_xyzt_units('mm');nib.save(n,p)
            full=reference_fingerprint(p)
            proxy=reference_fingerprint(p,native_voxel_limit=1000)
            self.assertTrue(full['native_voxel_hash_computed'])
            self.assertFalse(proxy['native_voxel_hash_computed'])
            self.assertIsNone(proxy['normalized_voxel_sha256'])
            self.assertFalse(proxy['all_native_voxels_checked'])
            result=rank(fingerprint(a,np.eye(4)),[dict(case_id='reference',fingerprint=proxy)])[0]
            self.assertEqual(result['match_type'],'APPROXIMATE_CANDIDATE')

if __name__=='__main__':unittest.main()
