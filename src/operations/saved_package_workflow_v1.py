"""Read-only saved-package integrity handoff. No inference, review decision or voxel decoding."""
import hashlib
import json
from pathlib import Path
import re

from src.operations.artifact_store import directory,read_file
from src.operations.workflow_plan_v1 import Stage,encoded,sha
from src.review.store import ReviewStore,FILES,digest


class SavedPackageReader(ReviewStore):
    """Reuse the production manifest contract without constructing a review writer."""
    def __init__(self,source):
        self.source=Path(source).absolute()
        fd=directory(self.source)
        try:
            import os
            s=os.fstat(fd);self.identity=(s.st_dev,s.st_ino)
        finally:os.close(fd)

    def reader(self,source):
        def read(name,cap):
            import os
            fd=directory(self.source)
            try:
                s=os.fstat(fd)
                if (s.st_dev,s.st_ino)!=self.identity:raise OSError('Saved-package root replaced')
                return read_file(fd,name,cap)
            finally:os.close(fd)
        return read


def inspect_package(reader,expected):
    raw,m,identity=reader.manifest('saved')
    if identity!=expected:raise ValueError('Saved manifest differs from requested pin')
    for key,name in FILES.items():
        ref=m['files'][key]
        data=reader.reader('saved')(name,64*1024**2 if key in ('ct','pred') else 1024**2)
        if len(data)!=ref['bytes'] or digest(data)!=ref['content_sha256']:
            raise ValueError('Saved package member differs from manifest')
    # Catch a changed manifest after reading its members, not just at the first read.
    if digest(reader.reader('saved')('manifest.json',1024**2))!=expected:
        raise ValueError('Saved manifest changed during inspection')
    return dict(schema='saved-package-integrity-v1',manifest_sha256=identity,
        case_package_id='case-package:'+identity,prediction_id='prediction:'+identity,
        prediction_mode=m['prediction_mode'],model_sha256=m['model_sha256'],
        members=m['files'],warnings=m['warnings'],
        qualification='byte-integrity-and-manifest-contract-only',
        voxel_geometry_checked=False,measurement_quality_checked=False)


def definition(source,expected_manifest_sha256):
    if not re.fullmatch('[a-f0-9]{64}',expected_manifest_sha256):raise ValueError('Explicit manifest SHA256 required')
    reader=SavedPackageReader(source)
    repo=Path(__file__).resolve().parents[2]
    paths=[Path(__file__),repo/'src/operations/workflow_plan_v1.py',
           repo/'src/operations/workflow_execution_v1.py',repo/'src/operations/artifact_store.py',repo/'src/review/store.py']
    producer=sha({str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    def validate_integrity(files):
        expected={'integrity.json':encoded(inspect_package(reader,expected_manifest_sha256))}
        if files!=expected:raise ValueError('Saved-package integrity descriptor differs')
        return {'manifest_sha256':expected_manifest_sha256,'scope':'saved-package-byte-integrity'}
    def handoff(integrity):
        return dict(schema='review-target-handoff-v1',case_package_id=integrity['case_package_id'],
            prediction_id=integrity['prediction_id'],manifest_sha256=integrity['manifest_sha256'],
            review_decision=None,measurement_qualification='not_evaluated',
            literature_answer='not_attached',source_revalidation_required_on_open=True)
    def produce_handoff(parents,config):
        validate_integrity(parents['integrity'])
        return {'handoff.json':encoded(handoff(json.loads(parents['integrity']['integrity.json'])))}
    def validate_handoff(files):
        current=inspect_package(reader,expected_manifest_sha256)
        if files!={'handoff.json':encoded(handoff(current))}:raise ValueError('Review handoff identity differs')
        return {'manifest_sha256':expected_manifest_sha256,'review_decision':None}
    stages=[Stage('integrity',inputs={'saved_manifest':expected_manifest_sha256},producer=producer),
            Stage('handoff',('integrity',),producer=producer)]
    handlers={'integrity':lambda p,c:{'integrity.json':encoded(inspect_package(reader,expected_manifest_sha256))},
              'handoff':produce_handoff}
    return stages,handlers,{'integrity':validate_integrity,'handoff':validate_handoff}
