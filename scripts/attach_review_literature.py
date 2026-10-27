#!/usr/bin/env python3
"""Explicit local attach/reopen for one exact review revision; no model calls."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.operations.artifact_store import directory, read_file
from src.review.store import ReviewStore
from src.review.literature_attachments_v1 import LiteratureAttachments


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['attach', 'reopen'])
    for key in ('root', 'reviews', 'node'):
        p.add_argument('--'+key, required=True, type=Path)
    p.add_argument('--capture', type=Path)
    for key in ('manifest-sha256', 'review-event-id', 'review-receipt-sha256', 'capture-sha256', 'artifact-id', 'receipt-sha256'):
        p.add_argument('--'+key)
    a = p.parse_args()
    required = ('capture','manifest_sha256','review_event_id','review_receipt_sha256','capture_sha256') if a.command == 'attach' else ('artifact_id','receipt_sha256')
    if not all(getattr(a,k) for k in required): p.error('Explicit identities and hashes required for '+a.command)
    try:
        # Never silently create a missing review store or output directory.
        for path in (a.root.absolute(), a.reviews.absolute()):
            fd = directory(path); os.close(fd)
        service = LiteratureAttachments(a.root, ReviewStore(a.reviews), node=a.node)
        if a.command == 'attach':
            path = a.capture.absolute(); fd = directory(path.parent)
            try: raw = read_file(fd, path.name, 1024**2)
            finally: os.close(fd)
            result = service.attach(manifest_sha256=a.manifest_sha256, review_event_id=a.review_event_id,
                review_receipt_sha256=a.review_receipt_sha256, capture=raw, capture_sha256=a.capture_sha256)
        else: result = service.reopen(a.artifact_id, a.receipt_sha256)
        print(json.dumps(result, sort_keys=True)); return 0
    except Exception as error:
        print(json.dumps({'error': str(error), 'automatic_retry': False}), file=sys.stderr); return 1


if __name__ == '__main__': raise SystemExit(main())
