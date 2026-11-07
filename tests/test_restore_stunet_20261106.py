import gzip,hashlib,io,tarfile,tempfile,unittest
from pathlib import Path
from scripts.acquisition.restore_stunet_sources_20261106 import extract


class RestoreTests(unittest.TestCase):
    def archive(self,p,name='PanTS_00000001/ct.nii.gz',duplicate=False):
        with tarfile.open(p,'w:gz') as f:
            for _ in range(2 if duplicate else 1):
                m=tarfile.TarInfo(name);m.size=3;f.addfile(m,io.BytesIO(b'abc'))

    def run_case(self,kind):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'a.tar.gz';out=root/'out';out.mkdir()
            self.archive(p,name='../evil' if kind=='unsafe' else 'PanTS_00000001/ct.nii.gz',duplicate=kind=='duplicate')
            expected={'PanTS_00000001':{'bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}}
            if kind=='hash':expected['PanTS_00000001']['sha256']='0'*64
            if kind=='crc':
                b=bytearray(p.read_bytes());b[-8]^=1;p.write_bytes(b)
            if kind=='ok':
                result=extract(p,expected,out,lambda:None,lambda *a,**k:None)
                self.assertEqual(Path(result['PanTS_00000001']['path']).read_bytes(),b'abc')
            else:
                with self.assertRaises((ValueError,gzip.BadGzipFile)):
                    extract(p,expected,out,lambda:None,lambda *a,**k:None)
                if kind=='hash':self.assertTrue((out/'PanTS_00000001.nii.gz.part').exists())

    def test_exact(self):self.run_case('ok')
    def test_hash_failure_preserved(self):self.run_case('hash')
    def test_crc_failure(self):self.run_case('crc')
    def test_duplicate(self):self.run_case('duplicate')
    def test_unsafe(self):self.run_case('unsafe')


if __name__=='__main__':unittest.main()
