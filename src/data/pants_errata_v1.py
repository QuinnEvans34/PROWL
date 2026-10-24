"""Explicit local correction of seven source-confirmed training masks only.

Not enabled in any frozen loader. Originals must remain intact. This is a local
derivative supported by upstream errata, not a redistributed upstream release.
"""
import numpy as np

VERSION='pants-issue12-local-normal-mask-1'
SOURCE='https://github.com/MrGiovanni/PanTS/issues/12#issuecomment-4538401573'
EXPECTED={f'PanTS_{n:08d}':v for n,v in [(3059,12),(44,16),(7933,16),(5693,20),(7947,32),(3548,36),(1819,45)]}


def corrected_mask(case_id, mask, *, role, original_sha256, expected_sha256):
    if role!='train' or case_id not in EXPECTED:
        raise ValueError('Correction requires an explicitly listed training case')
    if (not isinstance(expected_sha256,str) or len(expected_sha256)!=64
            or any(c not in '0123456789abcdef' for c in expected_sha256)
            or original_sha256!=expected_sha256):
        raise ValueError('Original source identity mismatch')
    if mask.dtype!=np.uint8 or mask.ndim!=3 or not np.isin(mask,[0,1]).all():
        raise ValueError('Decoded binary source required')
    if int(mask.sum())!=EXPECTED[case_id]:
        raise ValueError('Original lesion count differs from confirmed erratum')
    return np.zeros_like(mask)
