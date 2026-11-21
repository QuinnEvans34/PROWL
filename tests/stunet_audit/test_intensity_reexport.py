import unittest
import numpy as np
from scripts.stunet_audit.verify_intensity_reexport import hypotheses


class ReexportTests(unittest.TestCase):
    def test_clipped_integer_crop_requires_complete_identity(self):
        r=np.random.default_rng(42).uniform(-1500,2000,(12,13,14)).astype(np.float32)
        q=np.trunc(np.clip(r[:10,:11,:12],-999,999))
        out=hypotheses(q,r)
        exact=[x for x in out if x['exact_complete_query_identity']]
        self.assertTrue(any(x['rounding']=='truncate' and x['clipping']==[-999,999] for x in exact))
        q[0,0,0]+=1
        self.assertFalse(any(x['exact_complete_query_identity'] for x in hypotheses(q,r)))

    def test_unrelated_source_is_not_confirmed(self):
        rng=np.random.default_rng(7)
        self.assertFalse(any(x['exact_complete_query_identity'] for x in hypotheses(rng.normal(size=(10,10,10)),rng.normal(size=(12,12,12)))))
