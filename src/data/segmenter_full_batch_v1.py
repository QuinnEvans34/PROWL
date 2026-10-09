"""Portable full-trainer batch boundary with the historical NPY hash encoding.

Does not import the frozen six-case source resolver or its macOS diagnostic scripts.
"""
from io import BytesIO
import numpy as np
from src.data.manifest_records import digest
from src.data.source_inventory_records import require

_TOKEN = object()


def array_hash(array):
    stream = BytesIO()
    np.save(stream, array, allow_pickle=False)
    return digest(stream.getvalue())


class Batch:
    def __init__(self, token, *, study_id, role, operation, image, target, control_sha256):
        require(token is _TOKEN, 'Only a checked input provider can seal batches')
        self.study_id, self.role, self.operation = study_id, role, operation
        self.control_sha256 = control_sha256
        self.image = np.ascontiguousarray(image).copy()
        self.target = None if target is None else np.ascontiguousarray(target).copy()
        self._hashes = self.hashes()
        self._provenance = study_id, role, operation, control_sha256

    def hashes(self):
        return dict(image=array_hash(self.image), target=None if self.target is None else array_hash(self.target))

    def checked(self, control_sha256, operation, study_id):
        require((self.study_id, self.role, self.operation, self.control_sha256) == self._provenance
            and self.control_sha256 == control_sha256 and self.operation == operation
            and self.study_id == study_id and self.hashes() == self._hashes, 'Wrong/mutated batch provenance')
        require(operation != 'optimizer' or self.role == 'train', 'Evaluator batch cannot optimize')
        return self.image, self.target
