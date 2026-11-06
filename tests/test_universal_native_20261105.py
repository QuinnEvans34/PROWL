import unittest
import tempfile
from pathlib import Path
import numpy as np
from src.inference.universal_native_20261105 import native_probability, codes_from_probabilities, prepare_ct


class NativeTests(unittest.TestCase):
    def test_identity(self):
        x=np.zeros((7,8,9),np.float32);x[1:6,2:7,3:8]=.75
        np.testing.assert_array_equal(native_probability(x,np.eye(4),x.shape,np.eye(4)),x)
    def test_flipped_world_geometry(self):
        x=np.arange(24,dtype=np.float32).reshape(2,3,4)/24
        a=np.eye(4);a[0,0]=-1;a[0,3]=1
        np.testing.assert_array_equal(native_probability(x,a,x.shape,np.eye(4)),x[::-1])
    def test_crop_translation_and_background(self):
        a=np.eye(4);a[:3,3]=[2,3,1]
        actual=native_probability(np.ones((2,2,2),np.float32),a,(7,8,6),np.eye(4))
        expected=np.zeros((7,8,6));expected[2:4,3:5,1:3]=1
        np.testing.assert_array_equal(actual,expected)
    def test_threshold_and_overlap(self):
        np.testing.assert_array_equal(codes_from_probabilities(np.array([.5,.6,.9]),np.array([.5,.2,.8])),[0,1,2])
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):native_probability(np.full((2,2,2),np.nan),np.eye(4),(2,2,2),np.eye(4))
    def test_actual_preprocess_source_world_and_units(self):
        import nibabel as nib
        from src.inference.universal_model_loading_20261105 import digest
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'synthetic.nii.gz'
            affine=np.diag([-1.5,1.5,1.5,1.]);affine[:3,3]=[30.,-10.,50.]
            data=np.full((8,9,10),-175.,np.float32);data[2:6,2:7,2:8]=250.
            obj=nib.Nifti1Image(data,affine);obj.header.set_xyzt_units('mm');nib.save(obj,path)
            image,geometry=prepare_ct(path,digest(path),{'shape':list(data.shape),'affine':affine.tolist()})
            self.assertEqual(geometry['native_shape'],list(data.shape))
            self.assertFalse(geometry['reference_inputs_used'])
            restored=native_probability(image,np.array(geometry['working_affine']),data.shape,affine)
            np.testing.assert_allclose(restored,(data+175)/425,atol=1e-5)
            with self.assertRaises(ValueError):prepare_ct(path,'0'*64,{'shape':list(data.shape),'affine':affine.tolist()})


if __name__=='__main__':unittest.main()
