"""Human-operated, offline held-out validation; agents test invented inputs only.

No providers, network, database, model, tuning, encryption or backup operations.
Private paths are entered interactively outside an agent-connected terminal.
The development validator remains unable to read/accept held-out records.
"""
from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from .records import CONTRACTS, canonical_bytes
from .direct_ingestion import digest
from .development_set import FAMILIES, NEEDS, REFUSALS
from .public_exposure import prepared_public_preflight as public_preflight
from .corpus_inventory import frozen_inventory, verify_sources
from .labels import contains, gold_works, verify_label_set
from .query import make_query, normalize_question


class PrivateValidationError(ValueError):
    """Only fixed diagnostic text; never includes question/label values or paths."""


def seal_authored(suite):
    """Hash an explicitly authored revision; never supply questions or decisions."""
    result = deepcopy(suite)
    for case in result['cases']:
        case.pop('content_sha256', None)
        case['content_sha256'] = digest(case)
    result.pop('content_sha256', None)
    result['content_sha256'] = digest(result)
    return result


def _hash(record):
    if record['content_sha256'] != digest({k:v for k,v in record.items() if k!='content_sha256'}):
        raise PrivateValidationError('Content hash mismatch; prepare a separate revised copy after edits.')


def validate_private(suite, manifest, bundles, batches, *, bindings, exposed_questions, exposed_intents):
    """Mechanical validation only. Inputs/outputs stay in the human's private process."""
    try:
        return _validate_private(suite, manifest, bundles, batches, bindings=bindings,
                                 exposed_questions=exposed_questions, exposed_intents=exposed_intents)
    except PrivateValidationError:
        raise
    except (ValueError, KeyError, TypeError, IndexError):
        # Shared schema/query helpers may include offending values in their exceptions.
        raise PrivateValidationError('Private record structure, query, label or corpus validation failed.') from None


def _validate_private(suite, manifest, bundles, batches, *, bindings, exposed_questions, exposed_intents):
    version = suite.get('schema_version')
    schemas = {'prowl-private-evaluation-v1':'private-evaluation-v1.schema.json',
               'prowl-private-evaluation-v2':'private-evaluation-v2.schema.json'}
    if version not in schemas:
        raise PrivateValidationError('Unsupported private evaluation schema.')
    schema=json.loads((CONTRACTS/schemas[version]).read_text())
    try:
        Draft202012Validator(schema,format_checker=FormatChecker()).validate(suite)
    except ValidationError:
        raise PrivateValidationError('Private evaluation schema violation; check the closed schema.') from None
    _hash(suite)
    if version == 'prowl-private-evaluation-v2':
        roles = suite['roles']
        if (suite['source_draft_sha256'] != suite['reviewed_draft_sha256']
                or 'candidate_freeze_sha256' not in bindings
                or any(roles[k]['kind'] != 'human' or roles[k]['identity'] != 'Quinton Evans'
                       or roles[k]['model_version'] != 'not_applicable'
                       for k in ('semantic_reviewer','consistency_reviewer','private_operator'))
                or roles['question_author']['kind'] != 'ai_assistant'
                or roles['label_preparer']['kind'] != 'ai_assistant'
                or any(c['authorship']['basis'] != 'separate_ai_draft_human_reviewed'
                       for c in suite['cases'])):
            raise PrivateValidationError('Assisted roles or reviewed draft binding mismatch.')
    for key, expected in bindings.items():
        if suite[key] != expected:
            raise PrivateValidationError('Public corpus/development/exposure binding mismatch.')
    if suite['corpus_content_sha256'] != manifest['inventory']['content_sha256']:
        raise PrivateValidationError('Corpus content binding mismatch.')
    if frozen_inventory(batches) != manifest['inventory']:
        raise PrivateValidationError('Corpus inventory mismatch.')
    verify_sources(batches,bundles)
    reps=[b['representation'] for b in bundles]
    works={b['work']['work_id'] for b in bundles}
    passages=[x['record']['passage'] for b in batches for x in b['items']]
    public_wording={normalize_question(q).casefold() for q in exposed_questions}
    ids=set();wording=set();intents=set();sole=Counter();family=Counter();difficulty=Counter();counts=Counter()
    for case in suite['cases']:
        _hash(case)
        question=normalize_question(case['question']).casefold()
        if case['id'] in ids or question in wording or case['intent_group'] in intents:
            raise PrivateValidationError('Duplicate private identity, wording or intent group.')
        if question in public_wording or case['intent_group'] in exposed_intents:
            raise PrivateValidationError('Exact exposed wording or intent reused; revise privately before freeze.')
        ids.add(case['id']);wording.add(question);intents.add(case['intent_group'])
        if case['primary_need'] not in NEEDS or FAMILIES[case['primary_need'][1]] != case['family']:
            raise PrivateValidationError('Need/family mismatch.')
        # Structural validation only: a keyword gate must not set the expected answer.
        make_query(case['finding'],case['question'])
        label=verify_label_set(case['labels'],reps)
        concepts=[x['id'] for x in case['concepts']]
        if (label['question_id']!=case['id'] or concepts!=label['required_concepts']
                or len(set(concepts))!=len(concepts)):
            raise PrivateValidationError('Concept/question identity mismatch.')
        if any(v['grade']=='uncertain' for v in label['spans']):
            raise PrivateValidationError('Uncertain labels must be resolved privately.')
        direct=[v for v in label['spans'] if v['grade']=='direct']
        if (any(not v['concept_ids'] for v in direct)
                or {x for v in direct for x in v['concept_ids']} != set(concepts)):
            raise PrivateValidationError('Every required concept needs direct evidence.')
        if any(not any(contains(p,v) for p in passages) for v in direct):
            raise PrivateValidationError('A direct span is not fully contained in a frozen passage.')
        status=case['expected']['status'];reason=case['expected']['reason']
        if ((status=='answered') != label['answerable']
                or (status=='answered' and reason!='supported')
                or (status=='insufficient_evidence' and reason!='missing_evidence')
                or (status=='refused' and reason not in REFUSALS)):
            raise PrivateValidationError('Expected behavior and evidence disagree.')
        judgments=case['source_judgments'];seen={x['work_id'] for x in judgments}
        gold=gold_works(label,reps)
        if (len(seen)!=len(judgments) or not seen.issubset(works)
                or {x['work_id'] for x in judgments if x['grade']=='direct'} != gold):
            raise PrivateValidationError('Source judgments and gold evidence disagree.')
        if label['answerable']:
            if seen!=works:
                raise PrivateValidationError('Review every retained source for answerable cases.')
            family[case['family']]+=1
            if len(gold)==1:sole.update(gold)
        elif judgments:
            raise PrivateValidationError('Unsupported cases must not carry positive source judgments.')
        counts[status]+=1;difficulty[case['difficulty']]+=1
    if counts['answered']!=20 or counts['refused']+counts['insufficient_evidence']!=10:
        raise PrivateValidationError('Require 20 answerable and 10 unsupported/refused cases.')
    if set(family)!=set(FAMILIES.values()) or set(difficulty)!={'easy','paraphrase','multi_passage','limiting'}:
        raise PrivateValidationError('Cover every answerable family and all four difficulty categories.')
    # Protocol: avoid one paper being the sole gold support for most answerable cases.
    if max(sole.values(),default=0)>10:
        raise PrivateValidationError('One paper is sole support for more than half the answerable set.')
    return dict(state='private_mechanically_valid',private_content_sha256=suite['content_sha256'],
        schema_version=version, ai_assisted=version=='prowl-private-evaluation-v2',
        question_count=30,answerable_count=20,unsupported_or_refused_count=10,
        answerable_family_counts=dict(family),difficulty_counts=dict(difficulty),
        maximum_single_gold_source_question_count=max(sole.values(),default=0),unresolved_label_count=0,
        human_reviews_attested=True,protected_storage_verified=False,backup_verified=False,
        ready_for_tuning=False,
        limitation='Exact duplicate checks do not prove semantic independence. Human review assertions are not authenticated; no encryption or backup is verified.')


def prepare_assisted_quotes(suite, batches):
    """Convert operator-supplied exact passage quotes into labels, without model calls.

    This accepts no guessed offsets and makes no semantic judgments. The separate
    assistant supplies the structured transcription; Quinton never enters offsets.
    """
    try:
        result = deepcopy(suite)
        if result['schema_version'] != 'prowl-private-evaluation-v2':
            raise ValueError()
        passages = {i['record']['passage']['passage_id']:i['record']
                    for batch in batches for i in batch['items']}
        for case in result['cases']:
            if 'labels' in case:
                raise ValueError()
            evidence = case.pop('quote_evidence')
            if not isinstance(evidence,list) or len(evidence)>100:
                raise ValueError()
            spans = []
            for item in evidence:
                if set(item) != {'passage_id','quote','grade','concept_ids'}:
                    raise ValueError()
                record = passages[item['passage_id']]; p = record['passage']
                quote = item['quote']
                if not isinstance(quote,str) or not quote or len(quote)>8000:
                    raise ValueError()
                local = record['text'].find(quote)
                if local<0 or record['text'].find(quote,local+1)>=0:
                    raise ValueError()
                spans.append(dict(representation_id=p['representation_id'],
                    representation_sha256=p['representation_sha256'],
                    start=p['start']+local,end=p['start']+local+len(quote),
                    grade=item['grade'],concept_ids=item['concept_ids']))
            case['labels'] = dict(schema_version='1.0.0',question_id=case['id'],
                label_version='private-reviewed-v2',answerable=case['expected']['status']=='answered',
                required_concepts=[c['id'] for c in case['concepts']],spans=spans)
        return seal_authored(result)
    except (ValueError,KeyError,TypeError,AttributeError):
        raise PrivateValidationError('Exact quote preparation failed; review the transcription privately.') from None


def load_assisted_public_inputs(root):
    """Public-only inputs for mechanical preparation, never execution admission."""
    from .public_exposure import public_bytes, load_prepared_exposure, DIRECTORY
    from .development_set import checked_json
    public_preflight(root)
    exposure = load_prepared_exposure(root)
    freeze_path = DIRECTORY+'candidate-freeze-20261022.json'
    raw = public_bytes(root, freeze_path); freeze = json.loads(raw)
    _hash(freeze)
    if (freeze['version'] != 'prowl-candidate-freeze-20261022'
            or freeze['status'] != 'candidate_pinned_private_evaluation_not_admitted'):
        raise PrivateValidationError('Unexpected candidate freeze.')
    for pin in freeze['pins']:
        public_bytes(root,pin['path'],pin['sha256'])
    manifest_raw = public_bytes(root,'configs/evidence/corpus-disease-v1.json')
    manifest = json.loads(manifest_raw)
    suite = json.loads(public_bytes(root,DIRECTORY+'development-v6-draft.json'))
    from .records import sha256_hex
    bindings = {k:suite[k] for k in ('information_needs_sha256','information_needs_base_sha256')}
    bindings.update(corpus_manifest_sha256=sha256_hex(manifest_raw),
        corpus_content_sha256=manifest['inventory']['content_sha256'],
        final_development_content_sha256=suite['content_sha256'],
        public_exposure_manifest_sha256=sha256_hex(public_bytes(root,DIRECTORY+'public-exposure-v5.json')),
        candidate_freeze_sha256=sha256_hex(raw))
    if len(manifest['sources'])>32 or len(manifest['batches'])>256:
        raise PrivateValidationError('Public corpus bounds exceeded.')
    return (manifest,[checked_json(s['bundle'],root) for s in manifest['sources']],
        [checked_json(b,root) for b in manifest['batches']],bindings,
        [r['normalized_wording'] for r in exposure['inventory']['rows']],
        exposure['inventory']['intent_groups'])


def load_public_inputs(root):
    """Fail before any private read while expanded-scope evaluation is unready.

    The old ten-source loader is retired. A future version must bind a genuinely
    frozen revised development set; flipping a readiness flag cannot enable it.
    """
    public_preflight(root)
    raise PrivateValidationError(
        'Protected evaluation is not admitted. Complete the separate labeling tool, '
        'role schema, storage/backup and frozen admission before private authoring.')


def private_path(path, root):
    path=Path(path).expanduser()
    resolved=path.resolve(strict=True)
    if (resolved != path.absolute() or resolved.is_relative_to(Path(root).resolve())
            or not resolved.is_file() or resolved.stat().st_size>2*1024**2):
        raise PrivateValidationError('Use a bounded ordinary private file outside the repository, without symlinks.')
    return resolved


def write_private_result(folder, suite, report):
    """Exclusive owner-only output; never overwrite drafts/results."""
    folder.mkdir(mode=0o700,exist_ok=False)
    for name,value in [('validated-set.json',suite),('validation.json',report)]:
        fd=os.open(folder/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f:f.write(canonical_bytes(value))


def main():
    import argparse,getpass
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true',help='Hash the authored revision and write a separate validated copy; never supply review decisions.')
    parser.add_argument('--public-preflight',action='store_true',help='Report public readiness only; never prompt for or open private data.')
    parser.add_argument('--assisted-bindings',action='store_true',help='Print only current public preparation bindings for the separate assistant.')
    parser.add_argument('--prepare-assisted',action='store_true',help='Human-operated exact-quote preparation of AI-authored v2; no candidate requests or evaluation admission.')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    if sum((args.prepare,args.public_preflight,args.assisted_bindings,args.prepare_assisted))>1:
        parser.error('Choose one mode')
    if args.assisted_bindings:
        try:
            print(json.dumps(load_assisted_public_inputs(root)[3],indent=2))
        except (ValueError,OSError,KeyError,TypeError):
            raise SystemExit('Public assisted preparation bindings failed.') from None
        return
    if args.prepare_assisted:
        # Public checks and an actual operator terminal precede all private reads.
        try:
            manifest,bundles,batches,bindings,questions,intents=load_assisted_public_inputs(root)
        except (ValueError,OSError,KeyError,TypeError):
            raise SystemExit('Public assisted preparation checks failed.') from None
        if not sys.stdin.isatty():
            raise SystemExit('Run manually in a private terminal; redirected/agent input is refused.')
        print('Mechanical preparation only. No candidate requests, semantic decisions or evaluation admission.')
        if input('Private encrypted workspace and agent-disconnected terminal confirmed? Type PRIVATE: ')!='PRIVATE':
            raise SystemExit('Private session not confirmed.')
        try:
            path=private_path(getpass.getpass('Private AI transcription JSON path (hidden): '),root)
            draft=private_path(getpass.getpass('Original reviewed draft path (hidden): '),root)
            from .records import sha256_hex
            data=json.loads(path.read_text())
            draft_sha=sha256_hex(draft.read_bytes())
            if data['source_draft_sha256']!=draft_sha or data['reviewed_draft_sha256']!=draft_sha:
                raise PrivateValidationError('Original reviewed draft identity mismatch.')
            if input('Transcription preserves the reviewed questions, meanings and evidence; type REVIEWED: ')!='REVIEWED':
                raise PrivateValidationError('Transcription review not confirmed.')
            suite=prepare_assisted_quotes(data,batches)
            report=validate_private(suite,manifest,bundles,batches,bindings=bindings,
                exposed_questions=questions,exposed_intents=intents)
            report.update(ready_for_evaluation=False,original_draft_hash_verified=True)
            write_private_result(path.parent/(path.stem+'.validated'),suite,report)
        except PrivateValidationError as exc:
            raise SystemExit(str(exc)) from None
        except (ValueError,OSError,KeyError,TypeError):
            raise SystemExit('Private preparation failed. No inputs were overwritten; inspect privately.') from None
        print('Mechanical preparation passed; saved private output beside input. Storage/backup and single-run admission remain pending. No evaluation ran.')
        return
    if args.public_preflight:
        if args.prepare:parser.error('--public-preflight cannot be combined with --prepare')
        try:
            print(json.dumps(public_preflight(root),indent=2))
        except (ValueError,OSError,KeyError,TypeError):
            raise SystemExit('Public evaluation preflight failed; check public pins and reconciliation.') from None
        return
    # Public readiness precedes TTY checks, private path prompts and all private reads.
    try:
        manifest,bundles,batches,bindings,questions,intents=load_public_inputs(root)
    except (ValueError,OSError,KeyError,TypeError):
        raise SystemExit('Private authoring is not ready. Run --public-preflight for public status.') from None
    if not sys.stdin.isatty():
        raise SystemExit('Run manually in a private terminal; redirected/agent input is refused.')
    print('Human-only private session. No private content or paths should be shared with agents.')
    if input('Private encrypted workspace and agent-disconnected terminal confirmed? Type PRIVATE: ')!='PRIVATE':
        raise SystemExit('Private session not confirmed.')
    try:
        path=private_path(getpass.getpass('Private authored JSON path (hidden): '),root)
        suite=json.loads(path.read_text())
        if args.prepare:suite=seal_authored(suite)
        report=validate_private(suite,manifest,bundles,batches,bindings=bindings,
                                exposed_questions=questions,exposed_intents=intents)
        write_private_result(path.parent/(path.stem+'.validated'),suite,report)
    except PrivateValidationError as exc:
        raise SystemExit(str(exc)) from None
    except (ValueError,OSError,KeyError,TypeError):
        raise SystemExit('Private validation failed. Check input format, public pins and unused output directory; no input was overwritten.') from None
    print('Mechanical checks passed. Results saved beside the private input. Storage/backup/freeze remain separate; do not paste private files here.')


if __name__=='__main__':main()
