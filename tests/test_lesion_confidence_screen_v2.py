import unittest
import numpy as np
from src.inference.lesion_confidence_policy_v1 import THRESHOLDS, apply_policy
from src.inference.lesion_confidence_screen_v2 import encode, decode, pack, unpack, confidence_histogram


class ReplayTests(unittest.TestCase):
    def test_exact_policy_replay_on_random_probabilities(self):
        p = np.random.default_rng(42).random((3, 13, 17, 9), dtype=np.float32)
        p /= p.sum(0)
        c = encode(p)
        restored = unpack(pack(c), list(c.shape))
        np.testing.assert_array_equal(c, restored)
        for t in THRESHOLDS:
            np.testing.assert_array_equal(decode(restored, t), apply_policy(p, lesion_threshold=t))

    def test_boundaries_and_both_fallbacks(self):
        for t in THRESHOLDS[1:]:
            for x in (np.nextafter(np.float32(t), np.float32(0)), np.float32(t)):
                for fallback in (0, 1):
                    p = np.zeros((3, 1, 1, 1), np.float32)
                    p[2] = x
                    p[fallback] = (1-x)*.51
                    p[1-fallback] = (1-x)*.49
                    for threshold in THRESHOLDS:
                        np.testing.assert_array_equal(decode(encode(p), threshold),
                                                      apply_policy(p, lesion_threshold=threshold))

    def test_nonlesion_ties_preserved(self):
        p = np.full((3, 1, 1, 3), 1/3, np.float32)
        for t in THRESHOLDS:
            self.assertFalse(decode(encode(p), t).any())

    def test_every_code_and_odd_padding_roundtrip(self):
        for n in (1, 9, 10, 19):
            c = (np.arange(n, dtype=np.uint8) % 10).reshape(1, 1, n)
            self.assertEqual(pack(c).nbytes, (n+1)//2)
            np.testing.assert_array_equal(unpack(pack(c), list(c.shape)), c)

    def test_corrupt_storage_rejected(self):
        for packed, shape in ((np.array([255], np.uint8), [1, 1, 2]),
                              (np.array([16], np.uint8), [1, 1, 1]),
                              (np.array([], np.uint8), [1, 1, 1])):
            with self.assertRaises(ValueError):
                unpack(packed, shape)

    def test_histogram_splits_correct_and_incorrect_predictions(self):
        p = np.array([[.1,.1,.8], [.1,.1,.1], [.8,.8,.1]], np.float32).reshape(3,1,1,3)
        truth = np.array([1,0,1], np.uint8).reshape(1,1,3)
        h = confidence_histogram(p, truth)
        self.assertEqual(sum(h['true_positive']), 1)
        self.assertEqual(sum(h['false_positive']), 1)
        self.assertEqual(h['true_positive'][80], 1)
        self.assertEqual(h['false_positive'][80], 1)


if __name__ == '__main__':
    unittest.main()
