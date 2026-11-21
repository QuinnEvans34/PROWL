import unittest
import zipfile
import stat
from scripts.stunet_audit.extract_reference_ct import validate_members

def info(name,size=100):
    i=zipfile.ZipInfo(name);i.file_size=size;i.compress_size=size;i.CRC=0
    return i

class ArchiveTests(unittest.TestCase):
    def test_select_only_ct(self):
        ct,_=validate_members([info('dataset/s0001/ct.nii.gz'),info('dataset/s0001/segmentations/pancreas.nii.gz')],expected_ct=1)
        self.assertEqual([i.filename for i in ct],['dataset/s0001/ct.nii.gz'])
    def test_traversal_and_absolute_refused(self):
        for path in ('../ct.nii.gz','/ct.nii.gz','dataset/../ct.nii.gz','dataset\\ct.nii.gz'):
            with self.assertRaises(ValueError):validate_members([info(path)],expected_ct=1)
    def test_symlink_refused(self):
        i=info('dataset/s0001/ct.nii.gz');i.external_attr=(stat.S_IFLNK|0o777)<<16
        with self.assertRaises(ValueError):validate_members([i],expected_ct=1)
    def test_duplicates_and_large_members_refused(self):
        i=info('dataset/s0001/ct.nii.gz')
        with self.assertRaises(ValueError):validate_members([i,i],expected_ct=2)
        with self.assertRaises(ValueError):validate_members([info(i.filename,257*1024**2)],expected_ct=1)
    def test_original_count_required(self):
        with self.assertRaises(ValueError):validate_members([info('dataset/s0001/ct.nii.gz')])

if __name__=='__main__':unittest.main()
