"""Separate immutable literature attachments; never edit or create a review decision."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from src.operations.artifact_store import ArtifactStore, directory
from src.operations.case_literature_workflow_v1 import validate_capture, validator_identity
from src.review.store import digest, encode


def pin(value):
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('Explicit SHA256 required')
    return value


class LiteratureAttachments:
    def __init__(self, root, reviews, *, node, minimum_free_bytes=50_000_000_000):
        self.root = Path(root).absolute()
        self.reviews = reviews
        self.node = str(Path(node).resolve(strict=True))
        version = subprocess.run([self.node, '--version'], capture_output=True, text=True,
                                 timeout=5, check=True).stdout.strip()
        if not re.fullmatch(r'v\d+\.\d+\.\d+', version) or int(version.split('.')[0][1:]) < 24:
            raise ValueError('Node24 or newer required')
        self.policy = validator_identity()
        self.code = digest(Path(__file__).read_bytes())
        self.node_pin = digest(Path(self.node).read_bytes())
        self.identities = {}
        for path in (self.root, reviews.root):
            fd = directory(path)
            try:
                st = os.fstat(fd); self.identities[path] = (st.st_dev, st.st_ino)
            finally:
                os.close(fd)
        if self.root == reviews.root or reviews.root in self.root.parents or self.root in reviews.root.parents:
            raise ValueError('Use separate attachment and review roots')
        self.store = ArtifactStore(self.root, check_root=self.check_roots,
                                   max_bytes=2*1024**2, minimum_free_bytes=minimum_free_bytes)

    def check_roots(self):
        for path, expected in self.identities.items():
            fd = directory(path)
            try:
                st = os.fstat(fd)
                if (st.st_dev, st.st_ino) != expected:
                    raise ValueError('Attachment or review root changed')
            finally:
                os.close(fd)

    def review(self, manifest, event_id, receipt_pin):
        pin(manifest); pin(receipt_pin); self.check_roots()
        with self.reviews.locked():
            rows = self.reviews.history(manifest)
        matches = [r for r in rows if r['event']['review_event_id'] == event_id]
        if len(matches) != 1:
            raise ValueError('Exact saved review revision not found')
        record = matches[0]
        if digest(encode(record['receipt'])) != receipt_pin:
            raise ValueError('Review receipt pin mismatch')
        # Preserve only the owning store's public record, not its idempotency internals.
        return {'event': record['event'], 'receipt': record['receipt']}

    def validate(self, files):
        if set(files) != {'binding.json', 'capture.json', 'review.json'}:
            raise ValueError('Attachment inventory differs')
        raw = files['capture.json']
        if not isinstance(raw, bytes) or not 0 < len(raw) <= 1024**2:
            raise ValueError('Capture exceeds 1 MiB')
        binding = json.loads(files['binding.json'])
        expected_keys = {'schema', 'manifest_sha256', 'review_event_id', 'review_receipt_sha256',
                         'capture_sha256', 'validator_sha256', 'adapter_sha256', 'node_sha256',
                         'scope', 'decision_changed', 'measurement_qualification'}
        if set(binding) != expected_keys or binding['schema'] != 'review-literature-attachment-v1':
            raise ValueError('Invalid attachment binding')
        if (binding['scope'] != 'general-literature-associated-after-review'
                or binding['decision_changed'] is not False
                or binding['measurement_qualification'] != 'not_evaluated'):
            raise ValueError('Attachment scope changed')
        if (binding['validator_sha256'] != self.policy or validator_identity() != self.policy
                or binding['adapter_sha256'] != self.code or digest(Path(__file__).read_bytes()) != self.code
                or binding['node_sha256'] != self.node_pin or digest(Path(self.node).read_bytes()) != self.node_pin):
            raise ValueError('Attachment validator changed; explicit migration required')
        if digest(raw) != pin(binding['capture_sha256']):
            raise ValueError('Capture pin mismatch')
        review = self.review(binding['manifest_sha256'], binding['review_event_id'], binding['review_receipt_sha256'])
        if files['review.json'] != encode(review):
            raise ValueError('Attached review differs from saved revision')
        summary = validate_capture(raw, node=self.node)
        return {'binding_sha256': digest(files['binding.json']), 'capture_validation': summary}

    def attach(self, *, manifest_sha256, review_event_id, review_receipt_sha256, capture, capture_sha256):
        if not isinstance(capture, bytes) or not 0 < len(capture) <= 1024**2:
            raise ValueError('Capture exceeds 1 MiB')
        if digest(capture) != pin(capture_sha256):
            raise ValueError('Capture pin mismatch')
        review = self.review(manifest_sha256, review_event_id, review_receipt_sha256)
        binding = dict(schema='review-literature-attachment-v1', manifest_sha256=manifest_sha256,
                       review_event_id=review_event_id, review_receipt_sha256=review_receipt_sha256,
                       capture_sha256=capture_sha256, validator_sha256=self.policy,
                       adapter_sha256=self.code, node_sha256=self.node_pin,
                       scope='general-literature-associated-after-review', decision_changed=False,
                       measurement_qualification='not_evaluated')
        raw_binding = encode(binding); derivation = digest(raw_binding)
        artifact_id = 'review-literature:'+derivation
        files = {'binding.json': raw_binding, 'capture.json': capture, 'review.json': encode(review)}
        receipt, state = self.store.publish(artifact_id, derivation_sha256=derivation, files=files,
            metadata=dict(artifact_type='review-literature-attachment', schema_version='1.0.0',
                component='review-literature-v1', code_sha256=self.code,
                parents=[review_receipt_sha256, capture_sha256], retention='retain-with-review',
                sensitivity='research-local', run_id=artifact_id, stage_id='attach'), validate=self.validate)
        return dict(artifact_id=artifact_id, receipt_sha256=receipt, state=state,
                    manifest_sha256=manifest_sha256, review_event_id=review_event_id)

    def reopen(self, artifact_id, receipt_sha256):
        if not isinstance(artifact_id, str) or not re.fullmatch(r'review-literature:[a-f0-9]{64}', artifact_id):
            raise ValueError('Invalid attachment identity')
        files, receipt = self.store.resolve(artifact_id, receipt_sha256=pin(receipt_sha256),
            expected_derivation=artifact_id.split(':')[1], validate=self.validate)
        if digest(files['binding.json']) != artifact_id.split(':')[1]:
            raise ValueError('Attachment identity differs')
        return {'binding': json.loads(files['binding.json']), 'capture': json.loads(files['capture.json']),
                'review': json.loads(files['review.json']), 'receipt': receipt}
