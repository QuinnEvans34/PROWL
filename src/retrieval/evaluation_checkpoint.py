"""Public evaluation freeze checks. Never opens a protected question/label store.

Private authoring, semantic review and backup are human attestations; their truth
cannot be established from this content-free receipt. No model or tuning is run.
"""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from .records import CONTRACTS, sha256_hex
from .development_set import checked_json, validate_draft
from .development_review import validate_delta_review, read_public_json

FAMILIES = ('appearance', 'measurement', 'anatomy', 'ai_limits', 'review')
DIFFICULTIES = ('easy', 'paraphrase', 'multi_passage', 'limiting')
ATTESTATIONS = ('independent_authorship_attested', 'protected_content_mechanically_validated',
    'quinton_semantic_adjudication_complete', 'quinton_second_consistency_pass_complete',
    'cross_split_near_duplicate_review_complete', 'regression_exposure_review_complete',
    'source_concentration_review_complete', 'storage_allocation_confirmed',
    'independent_backup_hash_verified', 'protected_image_unmounted_after_freeze')


def validate_heldout_receipt(receipt, *, corpus_sha256, development_sha256):
    schema = json.loads((CONTRACTS / 'heldout-receipt-v2.schema.json').read_text())
    try:
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(receipt)
    except ValidationError:
        raise ValueError('Content-free receipt schema violation') from None
    if receipt['corpus_content_sha256'] != corpus_sha256:
        raise ValueError('Held-out receipt corpus binding mismatch')
    if receipt['status'] == 'not_created':
        nullable = [k for k, v in schema['properties'].items() if 'null' in v.get('type', [])]
        if any(receipt[k] is not None for k in nullable) or any(receipt[k] for k in ATTESTATIONS):
            raise ValueError('Blank receipt must not attest unfinished work')
        return dict(state='not_created', freeze_attested=False)
    if receipt['final_development_content_sha256'] != development_sha256:
        raise ValueError('Held-out receipt development binding mismatch')
    if any(receipt[k] is not True for k in ATTESTATIONS):
        raise ValueError('Held-out freeze attestations incomplete')
    required = ('protected_content_manifest_sha256', 'encrypted_image_sha256',
                'independent_encrypted_backup_sha256', 'freeze_date')
    if any(receipt[k] is None for k in required):
        raise ValueError('Held-out freeze identities incomplete')
    if receipt['encrypted_image_sha256'] != receipt['independent_encrypted_backup_sha256']:
        raise ValueError('Independent encrypted backup hash differs')
    if (receipt['question_count'], receipt['answerable_count'],
        receipt['unsupported_or_refused_count'], receipt['unresolved_label_count']) != (30,20,10,0):
        raise ValueError('Held-out counts or unresolved labels fail the protocol')
    families = receipt['answerable_family_counts']; difficulty = receipt['difficulty_counts']
    if families is None or sum(families.values()) != 20 or min(families.values()) < 1:
        raise ValueError('All answerable families must be represented')
    if difficulty is None or sum(difficulty.values()) != 30 or min(difficulty.values()) < 1:
        raise ValueError('All difficulty categories must be represented')
    concentration = receipt['maximum_single_gold_source_question_count']
    if concentration is None or concentration > 10:
        raise ValueError('Source concentration missing or one paper solely supports most answerable cases')
    return dict(state='freeze_attested', freeze_attested=True,
                limitation='Public structural checks and human attestations; no private content or backup was inspected by the agent.')


def checkpoint(root, receipt_name='heldout-receipt-template-v2.json'):
    root = Path(root).resolve()
    if receipt_name not in ('heldout-receipt-template-v2.json', 'heldout-receipt-v2.json'):
        raise ValueError('Only named public content-free receipts accepted')
    directory = root / 'configs/evidence/evaluation'
    path = directory / receipt_name
    if path.resolve().parent != directory.resolve() or path.stat().st_size > 65536:
        raise ValueError('Expected bounded public receipt, without external symlink')
    receipt = json.loads(path.read_text())
    # Reject extra fields before any output; never print rejected content.
    manifest_path = root / 'configs/evidence/corpus-coverage-v2.json'
    manifest = json.loads(manifest_path.read_text())
    suite = read_public_json(directory / 'development-v5-draft.json', root)
    heldout = validate_heldout_receipt(receipt, corpus_sha256=manifest['inventory']['content_sha256'],
                                     development_sha256=suite['content_sha256'])
    if len(manifest['sources']) > 32 or len(manifest['batches']) > 256:
        raise ValueError('Corpus count exceeds evaluation bound')
    mechanical = validate_draft(suite, manifest,
        [checked_json(s['bundle'], root) for s in manifest['sources']],
        [checked_json(b, root) for b in manifest['batches']],
        manifest_sha256=sha256_hex(manifest_path.read_bytes()),
        regression_sha256=sha256_hex((directory/'development-v1.json').read_bytes()),
        information_needs_sha256=sha256_hex((root/'docs/capstone/retrieval/planning/INFORMATION-NEEDS-V2.md').read_bytes()),
        information_needs_base_sha256=sha256_hex((root/'docs/capstone/retrieval/planning/INFORMATION-NEEDS.md').read_bytes()))
    doc = root / 'docs/capstone/retrieval'
    review = validate_delta_review(read_public_json(directory/'development-v5-human-review.json',root),suite,
        (doc/'DEVELOPMENT-QUESTIONS-AND-ANSWERS-V5.md').read_text(),
        prior_suite=read_public_json(directory/'development-v4-draft.json',root),
        prior_record=read_public_json(directory/'development-v4-human-review.json',root),
        prior_answers=(doc/'DEVELOPMENT-QUESTIONS-AND-ANSWERS.md').read_text())
    ready = review['development_review_attested_complete'] and heldout['freeze_attested']
    return dict(state='freeze_attested' if ready else 'checkpoint_pending',
        corpus_content_sha256=manifest['inventory']['content_sha256'],
        development_content_sha256=suite['content_sha256'],
        development_mechanical_state=mechanical['state'], review=review, heldout=heldout,
        ready_for_development_comparison=ready,
        limitation='Receipt validation does not authenticate human statements or inspect protected storage. This command never runs retrieval, generation or training.')


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt-name', choices=('heldout-receipt-template-v2.json','heldout-receipt-v2.json'), default='heldout-receipt-template-v2.json')
    p.add_argument('--require-ready', action='store_true')
    args=p.parse_args()
    try:
        result=checkpoint(Path(__file__).resolve().parents[2],args.receipt_name)
    except (ValueError,OSError,KeyError,TypeError):
        raise SystemExit('Public evaluation checkpoint validation failed.') from None
    print(json.dumps(result,indent=2))
    if args.require_ready and not result['ready_for_development_comparison']:
        raise SystemExit('Evaluation checkpoint pending: complete the explicit human review and protected freeze receipt.')


if __name__ == '__main__':
    main()
