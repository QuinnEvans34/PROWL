"""Additive metadata conversion for future render manifests; old renderer stays pinned."""
import numpy as np

def native_json(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:native_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [native_json(v) for v in value]
    return value
