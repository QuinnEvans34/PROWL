"""Invented content-free receipts only; never opens a protected store."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from src.retrieval.evaluation_checkpoint import validate_heldout_receipt, ATTESTATIONS, FAMILIES, DIFFICULTIES, checkpoint


def frozen():
    return dict(schema_version='prowl-heldout-receipt-v2',status='frozen',owner='Quinton Evans',
        corpus_content_sha256='a'*64,final_development_content_sha256='b'*64,
        protected_content_manifest_sha256='c'*64,encrypted_image_sha256='d'*64,
        independent_encrypted_backup_sha256='d'*64,question_count=30,answerable_count=20,
        unsupported_or_refused_count=10,answerable_family_counts=dict.fromkeys(FAMILIES,4),
        difficulty_counts=dict(easy=8,paraphrase=8,multi_passage=7,limiting=7),
        maximum_single_gold_source_question_count=4,unresolved_label_count=0,
        **dict.fromkeys(ATTESTATIONS,True),freeze_date='2026-10-18T00:00:00Z')


def check(r):
    return validate_heldout_receipt(r,corpus_sha256='a'*64,development_sha256='b'*64)


def test_valid_receipt_is_only_attestation():
    r=check(frozen());assert r['freeze_attested'] and 'no private content' in r['limitation']


@pytest.mark.parametrize('field',ATTESTATIONS)
def test_missing_attestation_never_freezes(field):
    r=frozen();r[field]=False
    with pytest.raises(ValueError):check(r)


@pytest.mark.parametrize('field,value',[
    ('corpus_content_sha256','e'*64),('final_development_content_sha256','e'*64),
    ('independent_encrypted_backup_sha256','e'*64),('question_count',29),
    ('answerable_count',19),('unresolved_label_count',1),('freeze_date',None),
    ('encrypted_image_sha256',None),('protected_content_manifest_sha256',None),
    ('answerable_family_counts',dict(appearance=0,measurement=8,anatomy=4,ai_limits=4,review=4)),
    ('difficulty_counts',dict(easy=0,paraphrase=16,multi_passage=7,limiting=7)),
    ('maximum_single_gold_source_question_count',None),
    ('question_count',True),('freeze_date','not-a-date'),
])
def test_invalid_bindings_counts_and_backup_refused(field,value):
    r=frozen();r[field]=value
    with pytest.raises(ValueError):check(r)


@pytest.mark.parametrize('field',['questions','labels','private_path','passphrase','source_ids','notes'])
def test_private_fields_refused_without_echo(field):
    r=frozen();r[field]='INVENTED_SECRET_CANARY'
    with pytest.raises(ValueError,match='^Content-free receipt schema violation$') as e:check(r)
    assert 'CANARY' not in str(e.value)


def test_blank_template_stays_pending():
    p=Path(__file__).resolve().parents[2]/'configs/evidence/evaluation/heldout-receipt-template-v2.json'
    r=json.loads(p.read_text());r['corpus_content_sha256']='a'*64
    assert check(r)==dict(state='not_created',freeze_attested=False)
    r['question_count']=30
    with pytest.raises(ValueError,match='Blank receipt'):check(r)


def test_private_receipt_path_rejected_before_open(tmp_path):
    with pytest.raises(ValueError,match='Only named public'):
        checkpoint(tmp_path,'/private/heldout.json')


def test_external_receipt_symlink_rejected_before_open(tmp_path):
    p=tmp_path/'configs/evidence/evaluation';p.mkdir(parents=True)
    (p/'heldout-receipt-v2.json').symlink_to(tmp_path/'private.json')
    with pytest.raises(ValueError,match='bounded public'):
        checkpoint(tmp_path,'heldout-receipt-v2.json')
