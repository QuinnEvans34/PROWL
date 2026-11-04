"""Explicit byte-identical CT relocation; original mask and geometry gates retained."""
from pathlib import Path
import nibabel as nib
from src.data.verifier_candidate_inputs_v1 import CandidateInputs
from src.training.experiment_config import sha256

class RelocatedCandidateInputs(CandidateInputs):
    def __init__(self, *, relocation, **kwargs):
        super().__init__(**kwargs)
        if relocation['status']!='BYTE_IDENTICAL_CT_RESTORATION_ONLY':raise ValueError('Unqualified relocation')
        self.relocation=relocation['cases']
        if not self.relocation or not set(self.relocation)<=set(self.roles):raise ValueError('Protected relocation membership')
        for n,r in self.relocation.items():
            if r['role']!=self.roles[n]:raise ValueError('Relocation role mismatch')

    def check(self,name,role,*,labels=False):
        super().check(name,role,labels=labels)
        if labels:raise ValueError('No lesion access in recovery export')
        if name not in self.relocation:raise ValueError('Case outside remaining export')

    def _object(self,name,kind,meta):
        if kind=='lesion':raise ValueError('No lesion access in recovery export')
        if name not in self.relocation:raise ValueError('Case outside remaining export')
        if kind!='ct':return super()._object(name,kind,meta)
        r=self.relocation[name];path=Path(r['path'])
        if r['sha256']!=meta['source_sha256']['ct'] or r['bytes']!=self.observations[name]['ct']['bytes']:
            raise ValueError('Relocation differs from original CT identity')
        if path.stat().st_size!=r['bytes'] or sha256(path)!=r['sha256']:raise ValueError('Restored CT changed')
        return nib.load(path)
