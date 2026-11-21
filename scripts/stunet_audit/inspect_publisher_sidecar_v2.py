"""Restricted publisher metadata reader with inert, size-checked NumPy records."""
import collections
import io
import json
import math
import pickle
from pathlib import Path
import subprocess
import numpy as np
from scripts.stunet_audit.confirm_cropped_images import digest


class InertArray:
    def __setstate__(self, state):
        if not isinstance(state, tuple) or len(state) != 5:
            raise pickle.UnpicklingError('Unexpected array state')
        version, shape, dtype, fortran, data = state
        dtype=np.dtype(dtype)
        if (version!=1 or not isinstance(shape,tuple) or len(shape)>3 or
            not all(isinstance(n,int) and 0<=n<=1024 for n in shape) or
            math.prod(shape)>1024 or dtype.kind not in 'iufb' or dtype.itemsize>8 or
            not isinstance(data,bytes) or len(data)!=math.prod(shape)*dtype.itemsize):
            raise pickle.UnpicklingError('Array metadata allocation/type bound')
        self.values=np.frombuffer(data,dtype=dtype).reshape(shape,order='F' if fortran else 'C').tolist()


def reconstruct(subtype, shape, dtype):
    if subtype is not InertArray or shape != (0,) or dtype != b'b':
        raise pickle.UnpicklingError('Unexpected reconstruction')
    return InertArray()


def scalar(dtype,data):
    dtype=np.dtype(dtype)
    if dtype.kind not in 'iufb' or dtype.itemsize>8 or not isinstance(data,bytes) or len(data)!=dtype.itemsize:
        raise pickle.UnpicklingError('Scalar metadata bound')
    return np.frombuffer(data,dtype=dtype,count=1)[0].item()


class SidecarReader(pickle.Unpickler):
    def find_class(self,module,name):
        allowed={('collections','OrderedDict'):collections.OrderedDict,
                 ('numpy','dtype'):np.dtype,('numpy','ndarray'):InertArray,
                 ('numpy.core.multiarray','scalar'):scalar,('numpy._core.multiarray','scalar'):scalar,
                 ('numpy.core.multiarray','_reconstruct'):reconstruct,('numpy._core.multiarray','_reconstruct'):reconstruct}
        if (module,name) not in allowed:raise pickle.UnpicklingError('Unapproved global')
        return allowed[module,name]
    def persistent_load(self,*args):raise pickle.UnpicklingError('External reference')


def read_metadata(data):
    if len(data)>8192:raise ValueError('Sidecar byte limit')
    return SidecarReader(io.BytesIO(data)).load()


def main():
    root=Path('/Volumes/PROWL-Data/PROWL/teachers/stunet-audit-20261106-source')
    p=root/'plan_files/base_ep4k.model.pkl';data=p.read_bytes()
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!='0652eaf5cafda6bc269942238c3695994f2dc4f0':raise ValueError('Source revision')
    if subprocess.check_output(['git','show','HEAD:plan_files/base_ep4k.model.pkl'],cwd=root)!=data:raise ValueError('Source blob differs')
    result=dict(source=str(p),sha256=digest(p),bytes=len(data),same_as_pinned_git_blob=True,
                unrestricted_pickle_used=False,inert_numpy_records=True,metadata=read_metadata(data),
                checkpoint_bound_case_ledger_present=False,patient_independence_verified=False)
    destination=Path('outputs/prowl/stunet-audit-20261106/followup-public-01/checkpoint-sidecar-v2.json')
    with destination.open('x') as f:json.dump(result,f,indent=2,default=lambda x:x.values if isinstance(x,InertArray) else int(x))
    print(destination)


if __name__=='__main__':main()
