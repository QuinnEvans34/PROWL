"""One-use duration transaction: durable checkpoints and native screens before advancing."""
from copy import deepcopy
from pathlib import Path
import json
import os
import time

from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as inputs, segmenter_duration_targets_v1 as targets
from src.training import segmenter_duration_session_v1 as core, segmenter_duration_policy_v1 as policy
from src.operations.segmenter_duration_storage_v1 import validate_capability, pin

TASK = "segmenter_duration_request_v1"
LIMITS = dict(total_seconds=3600, producer_seconds=2700, recovery_seconds=600,
              rss_bytes=12*1024**3, driver_bytes=12*1024**3, free_bytes=100*1024**3,
              output_bytes=64*1024**2)
UNIT_LIMITS = dict(total_seconds=300, producer_seconds=240, recovery_seconds=60,
                   rss_bytes=3*1024**3, driver_bytes=0, free_bytes=0, output_bytes=16*1024**2)
REQUEST_FIELDS = {"schema_version", "task", "kind", "experiment_id", "identity", "controls",
                  "checkpoint_steps", "screen_steps", "policy", "policy_sha256", "targets",
                  "source_pins", "runtime", "storage_capability", "storage_capability_sha256",
                  "limits", "readiness", "input_cache", "imports_allowed", "extension_allowed",
                  "recovery_policy", "screen_mode", "model_calls"}
REQUIRED_CODE = (
    'src/training/segmenter_duration_session_v1.py','src/training/segmenter_duration_executor_v1.py',
    'src/training/segmenter_duration_evidence_v1.py','src/data/segmenter_duration_targets_v1.py',
    'src/operations/segmenter_duration_backup_v1.py','src/operations/segmenter_duration_storage_v1.py',
    'src/operations/segmenter_duration_dispatch_v1.py','scripts/diagnostics/segmenter_duration_launch.py',
    'src/operations/segmenter_duration_readiness_v1.py','tests/test_segmenter_duration_readiness.py',
    'docs/capstone/imaging/SEGMENTER-DURATION-READINESS-CONTRACT-V1.md',
    'src/training/segmenter_duration_policy_v1.py','tests/segmenter_duration_fixtures.py',
    'tests/test_segmenter_duration_transaction.py','tests/test_segmenter_duration_executor.py',
    'tests/test_segmenter_duration_targets.py','tests/test_segmenter_duration_evidence_recovery.py',
    'tests/test_segmenter_duration_storage_dispatch.py',
    'docs/capstone/imaging/SEGMENTER-DURATION-EXECUTION-CONTRACT-V1.md','configs/local/roots.schema.json')
_GRANT = object()


def call_limits(kind):
    if kind == "unit": return dict(producer=dict(forwards=35,optimizer_calls=6),cold=dict(forwards=0,optimizer_calls=0))
    return dict(producer=dict(forwards=253,optimizer_calls=192),cold=dict(forwards=31 if kind=="native_rehearsal" else 30,optimizer_calls=1 if kind=="native_rehearsal" else 0))


class CallCounter:
    """Count attempted calls before model/optimizer entry, across restored sessions."""
    def __init__(self, limits): self.limits=deepcopy(limits);self.counts=dict(forwards=0,optimizer_calls=0)
    def hit(self,key):
        require(self.counts[key]<self.limits[key], "Model-call hard stop")
        self.counts[key]+=1
    def attach(self,session):
        session.model.register_forward_pre_hook(lambda *args:self.hit("forwards"))
        old=session.optimizer.step
        def step(*args,**kwargs):self.hit("optimizer_calls");return old(*args,**kwargs)
        session.optimizer.step=step
        return session


def policy_step(r,step):
    return {2:48,4:96,6:192}[step] if r["kind"]=="unit" else step


def assess_stage(r,record):
    assessment=policy.assess_screen(r["policy"],record,trusted_policy_sha256=r["policy_sha256"])
    if r["kind"]!="native_rehearsal":return assessment
    # Engineering stress qualification preserves the policy result, but cannot claim scientific quality.
    scope=targets.stage_scope(r["targets"],record["step"])
    require(set(record)=={"schema_version","policy_sha256","baseline_sha256","step","outcomes"}
            and record["schema_version"]=="1.0.0" and record["policy_sha256"]==r["policy_sha256"]
            and record["baseline_sha256"]==r["policy"]["baseline_sha256"]
            and len(record["outcomes"])==len(scope["cases"]),"Incomplete engineering native screen")
    for row,case in zip(record["outcomes"],scope["cases"]):
        require(set(row)==policy.ROW_FIELDS and row["case_id"]==case["study_id"]
                and row["role"]==("train" if case["protected_role"]=="train" else "report_only")
                and row["status"]=="valid" and row["reason"] is None and row["reported_metrics"] is None,
                "Failed/missing engineering outcome")
        c=row["counts"];require(set(c)==policy.COUNT_FIELDS,"Engineering count fields")
        matrix=c["confusion_matrix"]
        require(type(matrix) is list and len(matrix)==3 and all(type(v) is list and len(v)==3 and all(type(n) is int and n>=0 for n in v) for v in matrix)
                and sum(map(sum,matrix))==__import__('math').prod(case["descriptor"]["geometry"]["shape_xyz"]),"Engineering native confusion inventory")
        require(0<sum(map(sum,matrix))<=policy.MAX_VOXELS and type(c["voxel_volume_mm3"]) in (float,int)
                and __import__('math').isfinite(c["voxel_volume_mm3"]) and c["voxel_volume_mm3"]>0 and type(c["source_boundary_contact"]) is bool,"Engineering count bounds")
        import numpy as np
        volume=float(abs(np.linalg.det(np.asarray(case['descriptor']['geometry']['affine_ras']).reshape(4,4)[:3,:3])))
        require(c['voxel_volume_mm3']==volume and c['source_boundary_contact']==any(v['source_boundary_contact'] for v in case['reference_components'])
                and sum(matrix[1])==case['fidelity']['metrics']['pancreas_parenchyma']['native_voxels'] and sum(matrix[2])==case['fidelity']['metrics']['lesion']['native_voxels'],"Engineering source/reference geometry differs")
        require(type(c["components"]) is list and len(c["components"])==len(case["reference_components"]),"Engineering component inventory")
        for v,ref in zip(c["components"],case["reference_components"]):
            require(set(v)=={"component_id","reference_voxels","true_positive"} and type(v["component_id"]) is int and v["component_id"]==ref["component_id"] and type(v["reference_voxels"]) is int and v["reference_voxels"]==ref["native_voxels"] and type(v["true_positive"]) is int and 0<=v["true_positive"]<=v["reference_voxels"],"Engineering component counts")
        require(sum(v["reference_voxels"] for v in c["components"])==sum(matrix[2]) and sum(v["true_positive"] for v in c["components"])==matrix[2][2],"Engineering component partition")
    return dict(decision="continue" if record["step"]<192 else "terminal_insufficient",engineering_only=True,quality_acceptance=False,policy_result=assessment)


def validate_request(r):
    require(type(r) is dict and set(r) == REQUEST_FIELDS, "Duration request fields")
    require(r["schema_version"] == "1.0.0" and r["task"] == TASK
            and r["kind"] in ("unit", "native_rehearsal", "scientific")
            and type(r["experiment_id"]) is str and r["experiment_id"].startswith("DURATION-")
            and r["imports_allowed"] is False and r["extension_allowed"] is False,
            "Duration task/import/extension boundary")
    require(type(r["controls"]) is dict and all(type(v) is str for v in r["controls"].values()), "Control byte encoding")
    control = core.validate_controls(r["identity"], {n:v.encode() for n,v in r["controls"].items()})
    i = r["identity"]; unit = r["kind"] == "unit"; real = r["kind"] == "scientific"
    require(i["domain"] == ("qualified_real_cache" if real else "invented_arrays_only"), "Domain/job mismatch")
    require((unit and i["config"]["tensor_shape"] == [24]*3 and i["config"]["max_steps"] == 6 and i["device"] == "cpu")
            or (not unit and i["config"]["tensor_shape"] == [144]*3 and i["config"]["max_steps"] == 192 and i["device"] == "mps"), "Duration job/update/device envelope")
    cadence = [0,2,4,6] if unit else [0,48,96,144,192]
    require(r["checkpoint_steps"] == cadence and r["screen_steps"] == cadence[1:]
            and all(type(v) is int for v in r["checkpoint_steps"]+r["screen_steps"])
            and r["limits"] == (UNIT_LIMITS if unit else LIMITS), "Duration cadence/resource drift")
    require(r["screen_mode"] == ("engineering_native_counts" if r["kind"] == "native_rehearsal" else "duration_policy"), "Wrong screen authority/domain")
    require(r["model_calls"] == call_limits(r["kind"]) and all(type(v) is int for stage in r["model_calls"].values() for v in stage.values()), "Model-call scope drift")
    policy.validate_policy(r["policy"], trusted_policy_sha256=r["policy_sha256"])
    require(r["policy"]["train_case_ids"] == control["train"]
            and r["policy"]["report_case_id"] == control["validation"][0], "Policy/source role drift")
    require(json.loads(r["controls"]["source.json"]) == r["source_pins"]
            and json.loads(r["controls"]["environment.json"]) == r["runtime"]
            and type(r["source_pins"]) is dict and r["source_pins"]
            and all(type(n) is str and pin(v) for n,v in r["source_pins"].items()), "Source/runtime controls")
    if unit:
        require(r["storage_capability"] is None and r["storage_capability_sha256"] is None
                and r["targets"] == dict(domain="invented_unit_targets") and r["input_cache"] is None
                and r["readiness"] == dict(kind="invented_unit_only"), "Unit scope used native controls")
    else:
        require(set(REQUIRED_CODE)<=set(r["source_pins"]),"Missing complete duration source/test/contract closure")
        cap = validate_capability(canonical(r["storage_capability"]))
        require(digest(canonical(cap)) == r["storage_capability_sha256"]
                and cap["phase"] == ("real" if real else "rehearsal"), "Storage pin/phase")
        targets.validate_scope(r["targets"], control)
        require(r["targets"]["domain"] == ("original_native_targets" if real else "invented_native_targets"), "Original target domain")
        geometry = json.loads(r["controls"]["geometry.json"])
        require(geometry["target_scope_sha256"] == digest(canonical(r["targets"]))
                and geometry["stage"] == targets.STAGE, "Stage not bound to geometry")
        require(type(r["readiness"]) is dict and r["readiness"].get("kind") ==
                ("qualified_duration_native_v1" if real else "frozen_v5_numerics_v1")
                and pin(r["readiness"].get("acceptance_sha256")), "Missing independent readiness")
        if real:
            require(set(r["input_cache"]) == {"area", "acceptance_sha256", "request_sha256", "payload_bytes"}
                    and r["input_cache"] == dict(area="segmenter-input-cache",
                    acceptance_sha256="8b21315b14e38a6f582964a274d430ce768af9fb8348c8858c9ece62221125f3",
                    request_sha256="d84cdcdc828410ed4603dccf1bab29ecf6d0e9154f9a4f6f3f9f9cd0bc613364",payload_bytes=104509440)
                    and all(pin(r["readiness"].get(n)) for n in ("producer_sha256", "recovery_sha256", "tests_sha256")), "Qualified cache/native evidence")
        else: require(r["input_cache"] is None, "Native rehearsal cannot open actual cache")
    require(r["recovery_policy"] == dict(primary_denied=True, original_target_reads=0,
            original_ct_reads=0, real_optimizer_calls=0, automatic_restart=False), "Recovery scope expanded")
    return control


class Grant:
    def __init__(self, token, request_pin, identity_pin, approval_pin):
        require(token is _GRANT, "Only exact authorization can issue a duration grant")
        self.request_pin, self.identity_pin, self.approval_pin = request_pin, identity_pin, approval_pin


def authorize(r, approval_raw=None, *, trusted_approval_sha256=None):
    validate_request(r)
    if r["kind"] == "unit":
        require(approval_raw is None and trusted_approval_sha256 is None, "Unit fixture cannot use actual authority")
        return None
    require(type(approval_raw) is bytes and pin(trusted_approval_sha256)
            and digest(approval_raw) == trusted_approval_sha256, "Missing independently pinned job approval")
    a = json.loads(approval_raw)
    require(type(a) is dict and set(a) == {"kind", "author", "user_instruction", "request_sha256",
            "identity_sha256", "job_kind", "model_calls", "screen_mode", "original_target_reads", "original_ct_reads", "extension", "restart"}
            and a["kind"] == "exact_duration_job_v1" and a["author"] == "Quinton Evans"
            and type(a["user_instruction"]) is str and a["user_instruction"].strip()
            and a["request_sha256"] == digest(canonical(r)) and a["identity_sha256"] == digest(canonical(r["identity"]))
            and a["job_kind"] == r["kind"] and a["model_calls"] == r["model_calls"] and a["screen_mode"] == r["screen_mode"]
            and type(a["original_target_reads"]) is int and a["original_target_reads"] == (50 if r["kind"] == "scientific" else 0)
            and type(a["original_ct_reads"]) is int and a["original_ct_reads"] == 0
            and a["extension"] is False and a["restart"] is False, "Exact duration job scope differs")
    return Grant(_GRANT, a["request_sha256"], a["identity_sha256"], trusted_approval_sha256)


def checked_grant(r, grant):
    require(type(grant) is Grant and grant.request_pin == digest(canonical(r))
            and grant.identity_pin == digest(canonical(r["identity"])) and pin(grant.approval_pin), "Duration grant drift")


def put(path, raw):
    with Path(path).open("xb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    fd=os.open(Path(path).parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


class Journal:
    def __init__(self, path, request):
        self.stream = Path(path).open("xb"); self.previous = digest(canonical(request)); self.sequence = 0

    def append(self, row):
        raw = json.dumps(dict(sequence=self.sequence,previous_sha256=self.previous,event=row),sort_keys=True,separators=(",",":"),allow_nan=False).encode()
        self.stream.write(raw+b"\n"); self.stream.flush(); os.fsync(self.stream.fileno())
        self.previous = digest(raw); self.sequence += 1

    def close(self): self.stream.close()


def verify_journal(raw, request):
    previous = digest(canonical(request)); rows = []
    for n,line in enumerate(raw.splitlines()):
        r=json.loads(line)
        require(set(r)=={"sequence","previous_sha256","event"} and type(r["sequence"]) is int
                and r["sequence"]==n and r["previous_sha256"]==previous,"Duration journal chain")
        previous=digest(line);rows.append(r["event"])
    require(rows and rows[0]["state"]=="attempt_started","Missing attempt start")
    return rows,previous


def validate_checkpoint_reference(ref, session, boundary):
    require(type(ref) is dict and set(ref)=={"step","primary","backup","weights_sha256"}
            and type(ref["step"]) is int and ref["step"]==boundary
            and ref["primary"]["artifact_id"]==session.identity["run_id"]+":step:"+str(boundary)
            and ref["backup"]["artifact_id"]=="backup:"+ref["primary"]["artifact_id"]
            and all(pin(ref[k]["receipt_sha256"]) for k in ("primary","backup"))
            and ref["weights_sha256"]==core.numerical.state_hash(session.model.state_dict()),
            "Incomplete checkpoint/independent keeper")


def drive(r, session, provider, *, save_checkpoint, screen, event, guard, permit=None):
    """Shared scheduling loop; production enters only through execute's exact authorization."""
    refs=[];screens=[];probes={};next_weights=None;records=[];stopped=False
    names=json.loads(r["controls"]["inputs.json"])["train"]
    original=canonical(r)
    def check():
        guard();require(canonical(r)==original and not session.dirty,"Dirty/request-mutated transaction")
    for boundary in r["checkpoint_steps"]:
        while session.step<boundary:
            check();event(dict(state="update_started",step=session.step))
            row=session.update(provider,permit=permit);records.append(row);event(dict(state="update_complete",**row));check()
            if session.step==r["checkpoint_steps"][1]+1 and type(session) is core.Session:
                from src.training.segmenter_training_probe_v1 import encode_weights
                next_weights=dict(bytes=encode_weights(session.model),sha256=core.numerical.state_hash(session.model.state_dict()),state=core.payload(session))
        session.evaluate(provider);event(dict(state="tensor_evaluation_complete",step=session.step));check()
        ref=save_checkpoint(session)
        validate_checkpoint_reference(ref,session,boundary)
        refs.append(ref);event(dict(state="checkpoint_durable",step=session.step,reference=ref));check()
        b=provider.get(names[0],role="train",operation="inference");probes[boundary]=session.predict(b.image);check()
        if boundary in r["screen_steps"]:
            record,reference=screen(session,refs[-1],check)
            require(type(reference) is dict and set(reference)=={"step","screen_sha256","primary","backup"}
                    and reference["step"]==boundary and reference["screen_sha256"]==digest(canonical(record))
                    and reference["primary"]["artifact_id"]==session.identity["run_id"]+":screen:"+str(boundary)
                    and pin(reference["primary"]["receipt_sha256"]) and pin(reference["backup"]["receipt_sha256"])
                    and reference["backup"]["artifact_id"]=="backup:"+reference["primary"]["artifact_id"],"Undurable/mismatched native screen")
            assessment=assess_stage(r,record)
            ref=reference|dict(assessment=assessment);screens.append(ref)
            event(dict(state="native_screen_durable",step=boundary,reference=ref));check()
            if assessment["decision"]=="stopped":stopped=True;break
            require(assessment["decision"]==("continue" if boundary<session.config["max_steps"] else
                    assessment["decision"]) and (boundary<session.config["max_steps"] or
                    assessment["decision"] in ("terminal_pass","terminal_insufficient")),"Invalid native assessment transition")
    complete=session.step==session.config["max_steps"] and not stopped
    if complete:require(len(records)==session.step and all(sum(v["member_id"]==n for v in records)==session.step//6 for n in names),"Incomplete epoch exposure")
    result=dict(state="complete" if complete else "stopped",completed_steps=session.step,
        checkpoints=refs,screens=screens,exposure={n:sum(v["member_id"]==n for v in records) for n in names},
        last_durable_checkpoint=refs[-1] if refs else None,terminal_decision=screens[-1]["assessment"]["decision"] if screens else "stopped")
    return result,probes,next_weights


def execute(r, provider, dest, *, save_checkpoint, screen, protect_summary, finish,
            grant=None, guard=lambda:None, verify_source=None, session_factory=None):
    validate_request(r);unit=r["kind"]=="unit"
    require(type(provider) is (inputs.QualifiedInputs if r["kind"]=="scientific" else inputs.InventedInputs)
            and canonical(provider.control)==r["controls"]["inputs.json"].encode(),"Checked provider/control required")
    if not unit:checked_grant(r,grant);require(callable(verify_source),"Production pin verifier required")
    else:require(grant is None,"Wrong unit grant")
    require(session_factory is None or unit,"Production cannot inject a fake session")
    factory=session_factory or core.Session
    permit=core.UpdatePermit(core._REAL_LAUNCH_TOKEN,grant.identity_pin,grant.request_pin) if r["kind"]=="scientific" else None
    dest=Path(dest);require(dest.is_absolute() and dest.resolve(strict=True)==dest and dest.is_dir(),"Unsafe transaction destination")
    journal=Journal(dest/"journal.jsonl",r);s=None;refs=[];counter=None;start=time.monotonic()
    original=canonical(r)
    def check():
        guard();require(canonical(r)==original and time.monotonic()-start<r["limits"]["producer_seconds"],"Duration identity/time drift")
        if s is not None:require(s.identity==r["identity"] and s.config==r["identity"]["config"] and canonical(provider.control)==r["controls"]["inputs.json"].encode(),"Session/provider drift")
    def save(session):
        if verify_source:verify_source()
        ref=save_checkpoint(session);validate_checkpoint_reference(ref,session,session.step)
        if verify_source:verify_source()
        refs.append(ref);return ref
    def checked_screen(session,ref,tick):
        if verify_source:verify_source()
        result=screen(session,ref,tick)
        if verify_source:verify_source()
        return result
    try:
        journal.append(dict(state="attempt_started",request_sha256=digest(canonical(r)),step=0));check()
        if verify_source:verify_source()
        s=factory(r["identity"],{n:v.encode() for n,v in r["controls"].items()})
        counter=CallCounter(r["model_calls"]["producer"])
        if type(s) is core.Session:counter.attach(s)
        result,probes,next_weights=drive(r,s,provider,save_checkpoint=save,screen=checked_screen,event=journal.append,guard=check,permit=permit)
        extra=finish(s,result,probes,next_weights,check)|dict(model_calls=counter.counts);check()
        if verify_source:verify_source()
        journal.append(dict(state="transaction_verified",result=result));journal.close()
        raw=(dest/"journal.jsonl").read_bytes();_,last=verify_journal(raw,r)
        result=result|dict(task="segmenter_duration_run_summary_v1",request_sha256=digest(canonical(r)),
            identity_sha256=digest(canonical(r["identity"])),journal_sha256=digest(raw),last_event_sha256=last,
            seconds=float(time.monotonic()-start),recovery=extra)
        files={"request.json":canonical(r),"completion.json":canonical(result),"journal.jsonl":raw,
               "screens.json":canonical(extra["screen_records"])}
        from src.training.segmenter_duration_evidence_v1 import validate_summary
        validate_summary(files,r);protected=protect_summary(files,s.identity);check()
        put(dest/"transaction.json",canonical(result|dict(summary_reference=protected)))
        return result|dict(summary_reference=protected)
    except BaseException as exc:
        if s is not None:s.dirty=True
        failure=dict(state="consumed_incomplete",completed_steps=s.step if s is not None else 0,dirty=s.dirty if s is not None else False,model_calls=counter.counts if counter is not None else dict(forwards=0,optimizer_calls=0),
                     last_durable_checkpoint=refs[-1] if refs else None,error_type=type(exc).__name__,message=str(exc))
        if not journal.stream.closed:journal.append(failure|dict(state="failed_or_interrupted"))
        put(dest/"transaction-failure.json",canonical(failure));raise
    finally:journal.close()
