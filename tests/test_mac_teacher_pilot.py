import numpy as np
import pytest
from scripts.diagnostics.pilot_distillation_mac import check_geometry


def test_world_geometry_rejects_same_shape_wrong_translation():
    expected=dict(source_shape=[8,9,10],source_affine=np.eye(4).tolist())
    a=np.eye(4);a[0,3]=2
    with pytest.raises(ValueError,match='geometry'):check_geometry([8,9,10],a,expected)


def test_world_geometry_accepts_identity_and_rejects_axis_size_swap():
    expected=dict(source_shape=[8,9,10],source_affine=np.eye(4).tolist())
    check_geometry([8,9,10],np.eye(4),expected)
    with pytest.raises(ValueError,match='geometry'):check_geometry([10,9,8],np.eye(4),expected)
