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
from .records import CONTRACTS, canonical_bytes, sha256_hex
from .direct_ingestion import digest
from .development_set import checked_json, FAMILIES, NEEDS, REFUSALS
from .corpus_inventory import frozen_inventory, verify_sources
from .labels import contains, gold_works, verify_label_set
from .query import make_query, normalize_question


class PrivateValidationError(ValueError):
    """Only fixed diagnostic text; never includes question/label values or paths."""


def seal_authored(suite):
    """Hash an explicit human-authored revision; never supply questions or decisions."""
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
    schema=json.loads((CONTRACTS/'private-evaluation-v1.schema.json').read_text())
    try:
        Draft202012Validator(schema,format_checker=FormatChecker()).validate(suite)
    except ValidationError:
        raise PrivateValidationError('Private evaluation schema violation; check the closed schema.') from None
    _hash(suite)
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
        question_count=30,answerable_count=20,unsupported_or_refused_count=10,
        answerable_family_counts=dict(family),difficulty_counts=dict(difficulty),
        maximum_single_gold_source_question_count=max(sole.values(),default=0),unresolved_label_count=0,
        human_reviews_attested=True,protected_storage_verified=False,backup_verified=False,
        ready_for_tuning=False,
        limitation='Exact duplicate checks do not prove semantic independence. Human review assertions are not authenticated; no encryption or backup is verified.')


def load_public_inputs(root):
    """Read only named, bounded, hash-pinned public inputs; no private paths accepted."""
    root=Path(root).resolve();directory=root/'configs/evidence/evaluation'
    exposure_path=directory/'public-exposure-v1.json'
    exposure=json.loads(exposure_path.read_text())
    if len(exposure['files'])>16:raise ValueError('Exposure input count exceeds bound')
    questions=[];intents=set()
    for item in exposure['files']:
        path=(root/item['path']).resolve()
        if not path.is_relative_to(root) or path.stat().st_size>2*1024**2:
            raise ValueError('Expected bounded public exposure file')
        raw=path.read_bytes()
        if sha256_hex(raw)!=item['sha256']:raise ValueError('Exposure input changed')
        if item['kind']=='development':
            for case in json.loads(raw)['cases']:
                questions.append(case['question'])
                if case.get('intent_group'):intents.add(case['intent_group'])
        elif item['kind']=='demo_markdown':
            rows=[line.split('|')[1].strip() for line in raw.decode().splitlines() if line.startswith('| ')]
            questions += [q for q in rows if q in exposure['demo_questions']]
        else:raise ValueError('Unknown public exposure kind')
    if not set(exposure['demo_questions']).issubset(questions):raise ValueError('Demo exposure mismatch')
    path=root/'configs/evidence/corpus-coverage-v2.json';manifest=json.loads(path.read_text())
    if len(manifest['sources'])>32 or len(manifest['batches'])>256:raise ValueError('Corpus input bound exceeded')
    bundles=[checked_json(s['bundle'],root) for s in manifest['sources']]
    batches=[checked_json(b,root) for b in manifest['batches']]
    development=json.loads((directory/'development-v5-draft.json').read_text())
    bindings=dict(corpus_manifest_sha256=sha256_hex(path.read_bytes()),
        corpus_content_sha256=manifest['inventory']['content_sha256'],
        final_development_content_sha256=development['content_sha256'],
        public_exposure_manifest_sha256=sha256_hex(exposure_path.read_bytes()),
        information_needs_sha256=sha256_hex((root/'docs/capstone/retrieval/planning/INFORMATION-NEEDS-V2.md').read_bytes()),
        information_needs_base_sha256=sha256_hex((root/'docs/capstone/retrieval/planning/INFORMATION-NEEDS.md').read_bytes()))
    return manifest,bundles,batches,bindings,questions,intents


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
    args=parser.parse_args()
    if not sys.stdin.isatty():
        raise SystemExit('Run manually in a private terminal; redirected/agent input is refused.')
    root=Path(__file__).resolve().parents[2]
    print('Human-only private session. No private content or paths should be shared with agents.')
    if input('Private encrypted workspace and agent-disconnected terminal confirmed? Type PRIVATE: ')!='PRIVATE':
        raise SystemExit('Private session not confirmed.')
    try:
        path=private_path(getpass.getpass('Private authored JSON path (hidden): '),root)
        suite=json.loads(path.read_text())
        if args.prepare:suite=seal_authored(suite)
        manifest,bundles,batches,bindings,questions,intents=load_public_inputs(root)
        report=validate_private(suite,manifest,bundles,batches,bindings=bindings,
                                exposed_questions=questions,exposed_intents=intents)
        write_private_result(path.parent/(path.stem+'.validated'),suite,report)
    except PrivateValidationError as exc:
        raise SystemExit(str(exc)) from None
    except (ValueError,OSError,KeyError,TypeError):
        raise SystemExit('Private validation failed. Check input format, public pins and unused output directory; no input was overwritten.') from None
    print('Mechanical checks passed. Results saved beside the private input. Storage/backup/freeze remain separate; do not paste private files here.')


if __name__=='__main__':main()
