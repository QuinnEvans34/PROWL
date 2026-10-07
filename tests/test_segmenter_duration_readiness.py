"""DUR-03 metadata-only integration checks; no arrays, models or jobs."""
from copy import deepcopy
import json
import os
from pathlib import Path
import pytest
from src.data.manifest_records import digest
from src.operations import segmenter_duration_readiness_v1 as repair
from scripts.diagnostics import segmenter_duration_launch as launch
from scripts.diagnostics import segmenter_lowrate_native_qualification as prior
from scripts.diagnostics import segmenter_training_qualification as qualification
from src.operations.segmenter_duration_dispatch_v1 import verify_code
from src.training import segmenter_duration_executor_v1 as engine

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def accepted(monkeypatch):
    # Fail if a test accidentally introduces model/session work.
    def denied(*a,**k):raise AssertionError('Model/session work outside DUR-03')
    monkeypatch.setattr(launch.core,'make_identity',denied)
    monkeypatch.setattr(launch.core,'Session',denied)
    cpu=launch.metadata_result(prior.cpu.DEST,prior.CPU_PIN)
    native=launch.metadata_result(prior.DEST,'3e13f53adec249ed55a1fe5de7be126ad78e6002536f9ac7f6d9f7d74f26b391')
    pins=json.loads((ROOT/'outputs/prowl/SEGMENTER-DURATION-DUR02-20261007/protected-pins-final.json').read_bytes())
    for n,h in (cpu['source_pins']|native['source_pins']).items():pins.setdefault(n,repair.TRANSITIONS.get(n,(h,h))[1])
    pins.update(repair.PRODUCING_PROVENANCE)
    for n in engine.REQUIRED_CODE:pins[n]=digest((ROOT/n).read_bytes())
    return pins,cpu,native


def test_exact_six_transitions_and_closure(accepted):
    pins,cpu,native=accepted
    result=repair.reconcile(ROOT,pins,cpu,native)
    assert result['state']=='exact_historical_readiness_reconciled'
    assert len(result['accepted_transitions'])==6
    assert result['model_forwards']==result['optimizer_calls']==0


@pytest.mark.parametrize('name',sorted(repair.TRANSITIONS))
def test_each_transition_current_substitution_refused(accepted,name):
    pins,cpu,native=accepted;pins[name]='a'*64
    with pytest.raises(ValueError,match='closure differs'):repair.reconcile(ROOT,pins,cpu,native)


@pytest.mark.parametrize('name',sorted(repair.TRANSITIONS))
def test_each_transition_historical_substitution_refused(accepted,name):
    pins,cpu,native=accepted
    for row in (cpu,native):
        if name in row['source_pins']:row['source_pins'][name]='b'*64
    with pytest.raises(ValueError,match='closure differs'):repair.reconcile(ROOT,pins,cpu,native)


@pytest.mark.parametrize('name',['src/training/segmenter_training_session_v1.py','scripts/diagnostics/segmenter_training_qualification.py','configs/local/roots.schema.json'])
def test_missing_historical_closure_refused(accepted,name):
    pins,cpu,native=accepted;pins.pop(name)
    with pytest.raises(ValueError,match='closure differs'):repair.reconcile(ROOT,pins,cpu,native)


def test_unlisted_source_mutation_refused(accepted):
    pins,cpu,native=accepted;name='src/training/segmenter_training_session_v1.py';pins[name]='c'*64
    with pytest.raises(ValueError,match='closure differs'):repair.reconcile(ROOT,pins,cpu,native)


def test_inconsistent_shared_receipt_origin_refused(accepted):
    pins,cpu,native=accepted;name=next(iter(set(cpu['source_pins'])&set(native['source_pins'])));cpu['source_pins'][name]='a'*64
    with pytest.raises(ValueError,match='Inconsistent'):repair.reconcile(ROOT,pins,cpu,native)


@pytest.mark.parametrize('name',sorted(repair.PRODUCING_PROVENANCE))
def test_portable_dependency_missing_refused(accepted,name):
    pins,cpu,native=accepted;pins.pop(name)
    with pytest.raises(ValueError):repair.reconcile(ROOT,pins,cpu,native)


@pytest.mark.parametrize('name',sorted(repair.PROVENANCE))
def test_provenance_byte_forgery_refused(tmp_path,name):
    p=tmp_path/name;p.parent.mkdir(parents=True);p.write_bytes(b'forged metadata')
    with pytest.raises(ValueError,match='hash differs'):repair.read_pinned(tmp_path,name,repair.PROVENANCE[name])


@pytest.mark.parametrize('field',[('cpu','state'),('cpu','gate'),('native','state'),('native','producer'),('native','recovery')])
def test_prior_acceptance_state_substitution_refused(accepted,field):
    pins,cpu,native=accepted;row=cpu if field[0]=='cpu' else native
    row[field[1]]={'passed':False} if field[1]=='gate' else ({'state':'failed'} if field[1] in ('producer','recovery') else 'failed')
    with pytest.raises(ValueError,match='qualification missing'):repair.reconcile(ROOT,pins,cpu,native)


def launcher_request(accepted):
    return dict(kind='native_rehearsal',source_pins=accepted[0],runtime=qualification.runtime(),readiness=dict(acceptance_sha256=prior.CPU_PIN))


def test_actual_launcher_readiness_retained_metadata(accepted):
    launch.validate_readiness(launcher_request(accepted))


def test_launcher_runtime_substitution_refused(accepted):
    r=launcher_request(accepted);r['runtime']['threads']=4
    with pytest.raises(ValueError,match='environment drift'):launch.validate_readiness(r)


def test_launcher_fallback_substitution_refused(accepted,monkeypatch):
    r=launcher_request(accepted);monkeypatch.setenv('PYTORCH_ENABLE_MPS_FALLBACK','1')
    with pytest.raises(ValueError,match='environment drift'):launch.validate_readiness(r)


def test_launcher_acceptance_substitution_refused(accepted):
    r=launcher_request(accepted);r['readiness']['acceptance_sha256']='a'*64
    with pytest.raises(ValueError,match='readiness identity'):launch.validate_readiness(r)


def test_native_evidence_cannot_satisfy_scientific_readiness(accepted,monkeypatch):
    r=launcher_request(accepted);r['kind']='scientific'
    real=launch.read_control
    def read(path,pin,*args):
        if Path(path).name=='SEGMENTER-DURATION-NATIVE-READINESS.json':raise ValueError('No scientific native acceptance')
        return real(path,pin,*args)
    monkeypatch.setattr(launch,'read_control',read)
    with pytest.raises(ValueError,match='No scientific'):launch.validate_readiness(r)


def test_changed_complete_source_path_verification(accepted):
    pins,cpu,native=accepted
    pins['docs/capstone/imaging/SEGMENTER-DURATION-SOURCE-PATH-CONTRACT-V1.md']=digest((ROOT/'docs/capstone/imaging/SEGMENTER-DURATION-SOURCE-PATH-CONTRACT-V1.md').read_bytes())
    verify_code(dict(source_pins=pins))
    assert len(pins)==397


def test_full_launch_source_chain_without_models(accepted):
    r=launcher_request(accepted)
    verify_code(r)
    launch.validate_readiness(r)


SCRIPT_PATHS=tuple(json.loads((ROOT/'outputs/prowl/SEGMENTER-DURATION-DUR03-20261007/dispatcher-blocker.json').read_bytes())['required_script_paths'])


@pytest.mark.parametrize('name',SCRIPT_PATHS)
def test_script_path_exact_known_script_verifies(name):
    verify_code(dict(source_pins={name:digest((ROOT/name).read_bytes())}))


@pytest.mark.parametrize('name',SCRIPT_PATHS)
def test_script_path_hash_substitution_refuses(name):
    with pytest.raises(ValueError,match='identity changed'):verify_code(dict(source_pins={name:'a'*64}))


@pytest.mark.parametrize('name',['scripts/diagnostics/unapproved.py','scripts/unapproved.py','scripts/diagnostics/segmenter_duration_launch.py.npy','scripts/diagnostics/segmenter_duration_launch.py/../segmenter_duration_launch.py','/scripts/diagnostics/segmenter_duration_launch.py','outputs/patient.json','src/patient.nii.gz','tests/state.pt','configs/cache.npy'])
def test_script_path_unapproved_or_payload_refuses_before_open(name,monkeypatch):
    from src.operations import segmenter_duration_dispatch_v1 as dispatcher
    def denied(*a,**k):raise AssertionError('Disallowed source was opened')
    monkeypatch.setattr(dispatcher,'read_control',denied)
    with pytest.raises(ValueError,match='Code pin cannot'):verify_code(dict(source_pins={name:'a'*64}))


@pytest.mark.parametrize('unsafe',['symlink','hardlink','oversize'])
def test_script_path_safe_file_guards_retained(tmp_path,monkeypatch,unsafe):
    from src.operations import segmenter_duration_dispatch_v1 as dispatcher
    monkeypatch.setattr(dispatcher,'REPO',tmp_path);name='scripts/diagnostics/segmenter_duration_launch.py';path=tmp_path/name;path.parent.mkdir(parents=True);raw=b'no executable fixture calls'
    if unsafe=='symlink':
        other=tmp_path/'fixture.py';other.write_bytes(raw);path.symlink_to(other)
    elif unsafe=='hardlink':
        path.write_bytes(raw);os.link(path,tmp_path/'linked.py')
    else:raw=b'0'*(4*1024**2+1);path.write_bytes(raw)
    with pytest.raises(ValueError):verify_code(dict(source_pins={name:digest(raw)}))


def test_read_pinned_symlink_refused(tmp_path):
    p=tmp_path/'real.json';p.write_bytes(b'{}');(tmp_path/'link.json').symlink_to(p)
    with pytest.raises(ValueError,match='Unsafe'):repair.read_pinned(tmp_path,'link.json',digest(b'{}'))


def test_read_pinned_multiple_links_refused(tmp_path):
    p=tmp_path/'real.json';p.write_bytes(b'{}');os.link(p,tmp_path/'link.json')
    with pytest.raises(ValueError,match='type/size'):repair.read_pinned(tmp_path,'link.json',digest(b'{}'))


def test_read_pinned_size_refused(tmp_path):
    p=tmp_path/'large.json';p.write_bytes(b'0'*(4*1024**2+1))
    with pytest.raises(ValueError,match='type/size'):repair.read_pinned(tmp_path,'large.json',digest(p.read_bytes()))
