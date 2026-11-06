import unittest
from types import SimpleNamespace
from src.inference.universal_model_loading_20261105 import map_state, CHANNELS


def tensor(shape=(2, 3), dtype='float32'):
    return SimpleNamespace(shape=shape, dtype=dtype)


class StrictMappingTests(unittest.TestCase):
    def test_official_mapping(self):
        value = tensor()
        for key, target in [('swinViT.layers1.x', 'backbone.swinViT.layers1.x'),
                            ('encoder1.x', 'backbone.encoder1.x'),
                            ('decoder1.x', 'backbone.decoder1.x'),
                            ('controller.weight', 'controller.weight'),
                            ('organ_embedding', 'organ_embedding')]:
            self.assertIs(map_state({'module.'+key:value}, {target:value})[target], value)

    def test_no_random_missing_fill(self):
        with self.assertRaises(ValueError): map_state({}, {'encoder':tensor()})

    def test_no_unexpected(self):
        with self.assertRaises(ValueError): map_state({'module.x':tensor()}, {})

    def test_no_unprefixed_keys(self):
        with self.assertRaises(ValueError): map_state({'x':tensor()}, {'x':tensor()})

    def test_shape_and_dtype(self):
        for wrong in [tensor((3,2)), tensor(dtype='float16')]:
            with self.assertRaises(ValueError): map_state({'module.x':wrong}, {'x':tensor()})

    def test_channel_identity(self):
        self.assertEqual(CHANNELS, {'pancreas':10, 'pancreatic_tumor':27})


if __name__ == '__main__': unittest.main()
