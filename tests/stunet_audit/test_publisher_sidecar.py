import pickle
import unittest
import numpy as np
from scripts.stunet_audit.inspect_publisher_sidecar_v2 import read_metadata,InertArray


class PublisherSidecarTests(unittest.TestCase):
    def test_numeric_array_is_inert_and_exact(self):
        result=read_metadata(pickle.dumps({'patch':np.array([128,128,128],dtype=np.int64)},protocol=4))
        self.assertIsInstance(result['patch'],InertArray)
        self.assertEqual(result['patch'].values,[128,128,128])

    def test_executable_global_refused(self):
        class Payload:
            def __reduce__(self):return eval,('1+1',)
        with self.assertRaises(pickle.UnpicklingError):read_metadata(pickle.dumps(Payload()))

    def test_object_array_and_oversize_refused(self):
        with self.assertRaises(pickle.UnpicklingError):read_metadata(pickle.dumps(np.array([{}],dtype=object),protocol=4))
        with self.assertRaises(ValueError):read_metadata(b'0'*8193)
