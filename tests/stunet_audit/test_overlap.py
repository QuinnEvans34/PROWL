import tempfile
import unittest
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import nibabel as nib
import numpy as np
from scipy.ndimage import gaussian_filter, zoom

from scripts.stunet_audit.overlap import fingerprint, fingerprint_file, rank, reliable_id_candidates


def phantom(seed):
    rng=np.random.default_rng(seed)
    v=gaussian_filter(rng.normal(size=(48,48,48)),3)
    v=(v-v.min())/(v.max()-v.min())*700-200
    return v.astype(np.float32)


class FingerprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=phantom(12);cls.b=phantom(42)
        cls.affine=np.diag([1.5,1.5,2.,1.])
        cls.reference=fingerprint(cls.a,cls.affine)
        cls.other=fingerprint(cls.b,cls.affine)
        cls.refs=[dict(case_id="unrelated",fingerprint=cls.other),dict(case_id="original",fingerprint=cls.reference)]

    def check_related(self,array,affine):
        r=rank(fingerprint(array,affine),self.refs,top_k=2)
        self.assertEqual(r[0]["reference_id"],"original")
        self.assertGreater(r[0]["similarity"],.9)
        self.assertFalse(r[0]["patient_identity_confirmed"])
        self.assertFalse(r[0]["absence_proves_independence"])

    def test_orientation_roundtrip(self):
        n=nib.Nifti1Image(self.a,self.affine).as_reoriented(np.array([[2,-1],[0,1],[1,1]]))
        f=fingerprint(n.get_fdata(dtype=np.float32),n.affine)
        self.assertEqual(f["normalized_voxel_sha256"],self.reference["normalized_voxel_sha256"])
        self.check_related(n.get_fdata(dtype=np.float32),n.affine)

    def test_resampling(self):
        self.check_related(zoom(self.a,.75,order=1),np.diag([2.,2.,2/.75,1.]))

    def test_intensity_rescale_and_export(self):
        self.check_related(self.a*1.4+73,self.affine)

    def test_center_crop(self):
        a=self.affine.copy();a[:3,3]=self.affine[:3,:3]@np.array([12,12,12])
        self.check_related(self.a[12:36,12:36,12:36],a)

    def test_shifted_padded_scan(self):
        array=np.pad(self.a,((6,3),(2,5),(0,7)),constant_values=-1000)
        self.check_related(array,self.affine)

    def test_unrelated_negative_control(self):
        scores=rank(self.other,[dict(case_id="original",fingerprint=self.reference)])
        self.assertLess(scores[0]["similarity"],.9)

    def test_exact_file_evidence(self):
        a=dict(self.reference,file_sha256="a"*64)
        r=rank(a,[dict(case_id="copy",fingerprint=a)])[0]
        self.assertEqual(r["match_type"],"EXACT_FILE_EQUAL")
        self.assertFalse(r["patient_identity_confirmed"])

    def test_nonfinite_and_constant_refused(self):
        with self.assertRaises(ValueError):fingerprint(np.ones((12,12,12)),np.eye(4))
        with self.assertRaises(ValueError):fingerprint(np.full((12,12,12),np.nan),np.eye(4))
        with self.assertRaises(ValueError):fingerprint(self.a,np.zeros((4,4)))

    def test_file_requires_explicit_units(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"synthetic.nii.gz";n=nib.Nifti1Image(self.a,self.affine);nib.save(n,p)
            with self.assertRaises(ValueError):fingerprint_file(p)
            f=fingerprint_file(p,appearance_only_unknown_units=True)
            self.assertTrue(f['unknown_units_appearance_only'])
            self.assertFalse(f['physical_geometry_certified'])
            n.header.set_xyzt_units("mm");nib.save(n,p)
            self.assertEqual(fingerprint_file(p)["normalized_voxel_sha256"],self.reference["normalized_voxel_sha256"])

    def test_aliases_are_not_verified_patient_ids(self):
        a=dict(original_collection="TotalSegmentator",original_release="1.0",original_id="s0001")
        self.assertFalse(reliable_id_candidates(a,a))
        a["identity_verified"]=True;self.assertTrue(reliable_id_candidates(a,a))
        self.assertFalse(reliable_id_candidates(a,dict(a,original_release="2.0")))

    def test_empty_reference_not_clearance(self):
        self.assertEqual(rank(self.reference,[]),[])

    def test_voxel_hash_is_not_rounded(self):
        a=self.a.copy();a[0,0,0]+=0.0001
        self.assertNotEqual(fingerprint(a,self.affine)['normalized_voxel_sha256'],self.reference['normalized_voxel_sha256'])

    def test_cli_guards_and_success(self):
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory);image=d/'phantom.nii.gz'
            n=nib.Nifti1Image(self.a,self.affine);n.header.set_xyzt_units('mm');nib.save(n,image)
            sha=hashlib.sha256(image.read_bytes()).hexdigest()
            row=dict(path=str(image),sha256=sha)
            manifest=d/'manifest.json';out=d/'results'
            payload=dict(references=[dict(row,case_id='reference',role='pretraining_reference')],
                         queries=[dict(row,case_id='query',role='development')])
            def command(allow=True):
                manifest.write_text(json.dumps(payload));digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
                cmd=[sys.executable,'scripts/audit_stunet_overlap.py','--manifest',str(manifest),'--manifest-sha256',digest,
                     '--output',str(out),'--max-cases','2','--max-seconds','30']
                return cmd+(['--allow-image-reads'] if allow else [])
            self.assertNotEqual(subprocess.run(command(False),capture_output=True).returncode,0)
            self.assertFalse(out.exists())
            payload['queries'][0]['role']='test'
            self.assertNotEqual(subprocess.run(command(),capture_output=True).returncode,0)
            self.assertFalse(out.exists())
            payload['queries'][0]['role']='development'
            done=subprocess.run(command(),capture_output=True,text=True)
            self.assertEqual(done.returncode,0,done.stderr)
            r=json.loads((out/'candidates.json').read_text())[0]
            self.assertEqual(r['candidates'][0]['match_type'],'EXACT_FILE_EQUAL')
            self.assertEqual(r['classification'],'UNRESOLVED')
            self.assertNotEqual(subprocess.run(command(),capture_output=True).returncode,0)

    def test_cli_changed_source_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory);image=d/'phantom.nii.gz'
            n=nib.Nifti1Image(self.a,self.affine);n.header.set_xyzt_units('mm');nib.save(n,image)
            payload=dict(references=[],queries=[dict(case_id='q',path=str(image),sha256='0'*64,role='development')])
            p=d/'manifest.json';p.write_text(json.dumps(payload))
            cmd=[sys.executable,'scripts/audit_stunet_overlap.py','--manifest',str(p),'--manifest-sha256',hashlib.sha256(p.read_bytes()).hexdigest(),
                 '--output',str(d/'out'),'--max-cases','1','--max-seconds','30','--allow-image-reads']
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertFalse((d/'out'/'candidates.json').exists())


if __name__=="__main__":unittest.main()
