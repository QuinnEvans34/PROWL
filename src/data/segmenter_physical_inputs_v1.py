"""Physical-window provider layered on the verified native source loader."""
from copy import deepcopy
import numpy as np
from src.data.segmenter_native_inputs_v1 import NativeInputs,OptimizerWindows
from src.data.segmenter_native_windows_v1 import sample_origin
from src.data.segmenter_physical_windows_v1 import POLICY,physical_geometry,coverage_bank,sample_window
from src.data.manifest_records import canonical,digest


class PhysicalInputs(NativeInputs):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.control=deepcopy(self.control)
        self.control.update(version='physical-detail-inputs-1',policy=deepcopy(POLICY),
                            sampler_rng_namespace='native-windows-2')
        self.pin=digest(canonical(self.control))

    @staticmethod
    def describe(case):
        record=physical_geometry(case['geometry']);f=np.array(record['factors'])
        centers=[np.floor(f*(np.array(c)+.5)-.5).astype(int).tolist() for c in case['centers']]
        mask=case['target']==2 if case['positive'] else case['target']>0
        return record,centers,coverage_bank(mask,record)

    def window(self,name,*,role,operation,visit,seed):
        self.check_role(name,role,operation)
        if operation!='optimizer':raise ValueError('Inference cannot use target-driven windows')
        case=self.load(name,role=role,operation=operation)
        record,centers,coverage=self.describe(case)
        origin,kind=sample_origin(record['shape'],centers,visit=visit,seed=seed,case_id=name,coverage=coverage)
        image,transform=sample_window(case['image'],record,origin,order=1)
        target,_=sample_window(case['target'],record,origin,order=0)
        return image[None],target,transform,dict(origin=list(origin),kind=kind,visit=visit,geometry=record)


# The shared adapter calls provider.window and binds its control hash. It does not
# choose geometry itself; the checkpoint/session below binds the physical policy.
PhysicalOptimizerWindows=OptimizerWindows
