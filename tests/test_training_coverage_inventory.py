import numpy as np
from scripts.diagnostics.inventory_training_lesion_coverage import coverage


def test_full_and_partial_coverage():
    mask=np.zeros((10,10,10),dtype=np.uint8);mask[1:9,2:8,3:7]=1
    r=coverage(mask,[[0,0,0],[10,10,10]])
    assert r['coverage']==1 and r['lesion_box']==[[1,2,3],[9,8,7]]
    r=coverage(mask,[[5,0,0],[10,10,10]])
    assert r['coverage']==.5 and r['outside_voxels']==96
