"""S01: typed invented pretraining, fresh optimizer and same-run byte recovery.

Actual sources/providers have no branch in this version. Native execution and
independent storage recovery require separate qualification, not this codec.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
import json
import os
from pathlib import Path
import re

import monai
import numpy as np
import torch

from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as inputs
from src.models import segmenter_pretrained_initialization_v1 as initializer
from src.training import segmenter_session_v1 as numerical
from src.training import segmenter_v5_training_session_v1 as baseline
from src.training import segmenter_normalized_loss_v1 as loss
from src.training import segmenter_native_scoring_v1 as scoring

TASK = "pancreas_lesion_segmenter_pretrained_transaction_v1"
DOMAIN = "invented_arrays_only"
POLICY = baseline.POLICY
CONTROLS = {n + ".json": n + "_sha256" for n in
            ("inputs", "source", "environment", "geometry", "initialization", "lineage", "acceptance")}
CONTEXT = set(CONTROLS) - {"inputs.json", "initialization.json"}
_TOKEN = object()
ROOT = Path(__file__).resolve().parents[2]
PINS = {
    "src/data/segmenter_training_inputs_v1.py": "8a6c3d5f978e3f38b058908ecde5b96a78c7a11b76402f3f91e87aa330a2002b",
    "src/models/segmenter_pretrained_initialization_v1.py": "92f3cfae28658dc313a032d2eca05786aa37e418570efb21b74ad7cdcc4ebd18",
    "src/models/segmenter_source_values_v1.py": "38e1685cb53e9d36a9f449aad9554b4690d695a926227744e1ef85ca174acc8a",
    "src/models/segresnet.py": "d3fff9db229c3641aab2456a54cce64d7ebf08494a9fe1abef241cef7d8b722d",
    "src/training/segmenter_native_scoring_v1.py": "cd852f3e08b4f66ca8fa33f531ea4dc2620fb44469a7f0f8c194169d8934e0ef",
    "src/training/segmenter_normalized_loss_v1.py": "0a682a030f495001c93c779446e4fcdfde3eda33370cd509e3cf2503ed6501a4",
    "src/training/segmenter_session_v1.py": "0dbc18456a238c0a4dff30e6ec201bdb28e44b37c50bd2f7efa4e44c3b291a6d",
    "src/training/segmenter_v5_training_session_v1.py": "d6f9059c16c1f8b34261a63203bde5da7ec056d1dc782a2675b3f838366b5d36",
}


def code_sha256():
    return digest(Path(__file__).read_bytes())


def _pin(value):
    return type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None


def _fields(value, names, message):
    require(type(value) is dict and set(value) == set(names), message)


def _json(raw, maximum=1024**2):
    require(type(raw) is bytes and len(raw) <= maximum, "Control byte envelope")
    obj = json.loads(raw)
    require(type(obj) is dict and canonical(obj) == raw, "Noncanonical control encoding")
    return obj


def _dependencies():
    require(all(digest((ROOT / path).read_bytes()) == pin for path, pin in PINS.items()),
            "Pretrained session dependency changed")


def config(*, size=144, steps=48):
    return baseline.config(size=size, steps=steps) | {"schema_version": "segmenter-pretrained-config-1"}


def _recipe(c):
    return deepcopy(c) | {"schema_version": "segmenter-v5-training-config-1"}


def validate_config(c):
    require(type(c) is dict and c.get("schema_version") == "segmenter-pretrained-config-1",
            "Wrong pretrained configuration")
    baseline.validate_config(_recipe(c))
    require(type(c["seed"]) is int and type(c["learning_rate"]) is float and
            type(c["weight_decay"]) is float, "Pretrained recipe types")


def next_member(c, control, step):
    validate_config(c)
    return baseline.next_member(_recipe(c), control, step)


def _fresh(c):
    validate_config(c)
    require(torch.get_default_device().type == "cpu" and torch.get_default_dtype() == torch.float32,
            "Pretrained ambient tensor defaults")
    return baseline.scratch(_recipe(c))


def fixture_context(audit, c):
    """Canonical invented controls; these explicitly deny actual training eligibility."""
    validate_config(c)
    r = initializer.validate_initialization(audit)
    return {
        "source.json": canonical(dict(domain=initializer.DOMAIN, source_sha256=r["source_sha256"],
            values_report_sha256=r["values_report_sha256"], generated=True)),
        "environment.json": canonical(dict(torch=str(torch.__version__), monai=str(monai.__version__),
            session_sha256=code_sha256(), helpers=PINS)),
        "geometry.json": canonical(dict(domain=DOMAIN, tensor_shape=c["tensor_shape"],
            roi_source="invented", original_arrays_read=0, jitter="none")),
        "lineage.json": canonical(dict(task=TASK, policy=initializer.POLICY, teacher_models=[],
            prior_task_imports=[], source_sha256=r["source_sha256"],
            source_backbone_sha256=r["source_backbone_sha256"], fresh_head_sha256=r["fresh_head_sha256"])),
        "acceptance.json": canonical(dict(domain=DOMAIN, status="invented_fixture_only",
            actual_source_accepted=False, training_eligible=False)),
    }


def make_identity(c, provider, controls, initialization_audit, *, run_id, device):
    validate_config(c)
    require(type(provider) is inputs.InventedInputs and type(controls) is dict and set(controls) == CONTEXT,
            "Invented provider and explicit context required")
    r = initializer.validate_initialization(initialization_audit)
    require(controls == fixture_context(initialization_audit, c), "Generated source/context mismatch")
    files = deepcopy(controls) | {"inputs.json": canonical(provider.control),
                                 "initialization.json": canonical(r)}
    identity = dict(schema_version="segmenter-pretrained-session-1", task=TASK, domain=DOMAIN,
        run_id=run_id, device=device, config=deepcopy(c),
        **{key: digest(files[name]) for name, key in CONTROLS.items()})
    validate_controls(identity, files)
    return identity, files


def validate_identity(i):
    _fields(i, {"schema_version", "task", "domain", "run_id", "device", "config"} |
            set(CONTROLS.values()), "Wrong pretrained identity fields")
    require(i["schema_version"] == "segmenter-pretrained-session-1" and i["task"] == TASK and
            i["domain"] == DOMAIN and i["device"] in ("cpu", "mps") and
            type(i["run_id"]) is str and re.fullmatch(r"segmenter-pretrained-[A-Za-z0-9_-]{1,80}", i["run_id"]),
            "Actual or wrong-task pretrained identity refused")
    validate_config(i["config"])
    require(all(_pin(i[k]) for k in CONTROLS.values()), "Invalid pretrained control pin")


def validate_controls(i, files):
    validate_identity(i)
    require(type(files) is dict and set(files) == set(CONTROLS), "Pretrained control inventory")
    require(all(type(files[n]) is bytes and digest(files[n]) == i[k] for n, k in CONTROLS.items()),
            "Pretrained control changed")
    c = {n: _json(v) for n, v in files.items()}
    a = c["acceptance.json"]
    require(a == dict(domain=DOMAIN, status="invented_fixture_only",
                     actual_source_accepted=False, training_eligible=False) and
            a["actual_source_accepted"] is False and a["training_eligible"] is False,
            "Actual source acceptance unavailable")
    r = c["initialization.json"]
    _fields(r, ("schema_version", "domain", "status", "scope", "execution_authority", "training_eligible",
        "control_sha256", "code_sha256", "values_code_sha256", "values_report_sha256", "factory_sha256",
        "source_sha256", "source_state_sha256", "source_backbone_sha256", "fresh_head_sha256",
        "target_state_sha256", "seed", "target_architecture", "policy", "excluded_keys", "model", "bytes"),
        "Initialization report inventory")
    require(r["schema_version"] == initializer.REPORT_VERSION and r["domain"] == initializer.DOMAIN and
        r["status"] == "pass" and r["scope"] == "invented_initialization_only" and
        r["execution_authority"] == "none" and r["training_eligible"] is False and
        type(r["seed"]) is int and r["seed"] == 42 and r["policy"] == initializer.POLICY and
        r["excluded_keys"] == list(initializer.HEAD_KEYS), "Unqualified initialization report")
    require(r["source_sha256"] != initializer.values.meta.ACTUAL_CANDIDATE_SHA and
            all(_pin(r[k]) for k in ("source_sha256", "source_state_sha256", "source_backbone_sha256",
                "fresh_head_sha256", "target_state_sha256", "control_sha256", "values_report_sha256")),
            "Actual or invalid source identity refused")
    require(r["code_sha256"] == PINS["src/models/segmenter_pretrained_initialization_v1.py"] and
            r["values_code_sha256"] == initializer.VALUES_PIN and r["factory_sha256"] == initializer.FACTORY_PIN,
            "Initialization dependency identity")
    initializer._architecture_check(r["target_architecture"])
    rows = r["model"]
    require(initializer._shape_rows(rows) == initializer.signature() and
            initializer.values.digest(rows) == r["target_state_sha256"] and
            initializer.values.digest(initializer._select(rows, False)) == r["source_backbone_sha256"] and
            initializer.values.digest(initializer._select(rows, True)) == r["fresh_head_sha256"] and
            r["bytes"] == dict(source=18805696, source_head=2176, backbone=18803520,
                              fresh_head=204, target=18803724), "Initialization inventory/digests")
    require(c["source.json"] == dict(domain=initializer.DOMAIN, source_sha256=r["source_sha256"],
        values_report_sha256=r["values_report_sha256"], generated=True) and
        c["source.json"]["generated"] is True, "Source/control substitution")
    require(c["environment.json"] == dict(torch=str(torch.__version__), monai=str(monai.__version__),
        session_sha256=code_sha256(), helpers=PINS), "Environment/code substitution")
    require(c["geometry.json"] == dict(domain=DOMAIN, tensor_shape=i["config"]["tensor_shape"],
        roi_source="invented", original_arrays_read=0, jitter="none") and
        type(c["geometry.json"]["original_arrays_read"]) is int, "Geometry/domain substitution")
    require(c["lineage.json"] == dict(task=TASK, policy=initializer.POLICY, teacher_models=[],
        prior_task_imports=[], source_sha256=r["source_sha256"], source_backbone_sha256=r["source_backbone_sha256"],
        fresh_head_sha256=r["fresh_head_sha256"]), "Source/head lineage substitution")
    control = c["inputs.json"]
    _fields(control, ("target_metadata", "domain", "fixture_version", "size", "train", "validation",
        "member_sha256", "roi_source", "jitter", "original_arrays_read"), "Input control fields")
    require(control["domain"] == DOMAIN and control["fixture_version"] == "class_cues_six_members_v1" and
        type(control["size"]) is int and control["size"] == i["config"]["tensor_shape"][0] and
        control["train"] == [f"invented-train-{n}" for n in range(6)] and
        control["validation"] == ["invented-validation"] and control["roi_source"] == "invented" and
        control["jitter"] == "none" and type(control["original_arrays_read"]) is int and
        control["original_arrays_read"] == 0, "Input role/domain/geometry substitution")
    names = set(control["train"] + control["validation"])
    require(set(control["target_metadata"]) == set(control["member_sha256"]) == names and
        all(set(row) == {"image", "target"} and all(_pin(v) for v in row.values())
            for row in control["member_sha256"].values()), "Input member inventory")
    _dependencies()
    return control


@dataclass(frozen=True)
class InventedPermit:
    identity_sha256: str
    request_sha256: str
    _token: object


def invented_permit(identity, request_sha256):
    validate_identity(identity)
    require(_pin(request_sha256), "Missing invented request identity")
    return InventedPermit(digest(canonical(identity)), request_sha256, _TOKEN)


class Session:
    def __init__(self, identity, controls, initialization_audit):
        self.control = validate_controls(identity, controls)
        report = initializer.validate_initialization(initialization_audit)
        require(canonical(report) == controls["initialization.json"], "Typed source differs from session")
        self._setup(identity, controls)
        self.model.load_state_dict(dict(initialization_audit.state), strict=True)
        require(initializer.values.state_rows(dict(self.model.state_dict())) == report["model"],
                "Initial backbone/head transfer mismatch")
        self._activate(identity["device"])

    def _setup(self, identity, controls):
        self.identity, self.controls = deepcopy(identity), deepcopy(controls)
        self.config = deepcopy(identity["config"])
        self.control = validate_controls(identity, controls)
        self.model = _fresh(self.config)
        self.device = "cpu"
        self.step, self.dirty, self.history, self.evaluations = 0, False, [], []
        self.cpu_rng = torch.Generator().manual_seed(42).get_state()
        self.mps_rng = None
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.config["learning_rate"],
                                          weight_decay=self.config["weight_decay"])

    def _activate(self, device):
        if device == "mps":
            require(os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") == "0" and torch.backends.mps.is_available(),
                    "Native MPS/no fallback required")
            old = torch.mps.get_rng_state()
            try:
                torch.mps.manual_seed(42)
                self.mps_rng = torch.mps.get_rng_state().cpu().clone()
            finally:
                torch.mps.set_rng_state(old)
            self.model.to(device)
            # The optimizer is new: create it over the moved parameters before any update.
            self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.config["learning_rate"],
                                              weight_decay=self.config["weight_decay"])
        self.device = device

    def _clean(self):
        require(not self.dirty and self.config == self.identity["config"], "Dirty or changed session")
        validate_controls(self.identity, self.controls)

    def _provider(self, provider):
        require(type(provider) is inputs.InventedInputs, "Actual or raw input provider refused")
        require(canonical(provider.control) == self.controls["inputs.json"], "Changed input provider")

    def import_weights(self, *args, **kwargs):
        raise ValueError("Typed step0 initialization or complete same-run recovery only")

    def update(self, provider, *, exact_permit):
        self._clean()
        require(type(exact_permit) is InventedPermit and exact_permit._token is _TOKEN and
            exact_permit.identity_sha256 == digest(canonical(self.identity)) and _pin(exact_permit.request_sha256),
            "Exact invented update permit required")
        self._provider(provider)
        name, trace = next_member(self.config, self.control, self.step)
        batch = provider.get(name, role="train", operation="optimizer")
        require(type(batch) is inputs.Batch, "Unsealed optimizer batch")
        x, y = batch.checked(self.identity["inputs_sha256"], "optimizer", name)
        batch_hashes = batch.hashes()
        x, y = torch.as_tensor(x), torch.as_tensor(y, dtype=torch.long)
        require(x.device.type == y.device.type == "cpu" and x.dtype == torch.float32 and
            x.shape == (1, *self.config["tensor_shape"]) and y.shape == tuple(self.config["tensor_shape"]) and
            torch.isfinite(x).all() and x.min() >= 0 and x.max() <= 1 and ((y >= 0) & (y <= 2)).all(),
            "Invalid optimizer input")
        self.dirty = True
        with self.rng_scope():
            self.model.train()
            self.optimizer.zero_grad(set_to_none=True)
            value = loss.objective(self.model(x[None].to(self.device)), y[None].to(self.device), self.config["loss_id"])
            require(torch.isfinite(value).item(), "Nonfinite loss")
            value.backward()
            require(all(p.grad is not None and torch.isfinite(p.grad).all().item()
                        for p in self.model.parameters()), "Nonfinite/missing gradient")
            self.optimizer.step()
            require(numerical.finite(self.model.state_dict()) and numerical.finite(self.optimizer.state_dict()),
                    "Nonfinite mutated state")
            row = dict(completed_step=self.step + 1, member_id=name, sampling=trace,
                loss=float(value.detach().cpu()), learning_rate=self.optimizer.param_groups[0]["lr"],
                batch_sha256=batch_hashes)
        # Validate the whole prospective accounting before clearing dirty.
        candidate = progress(self)
        candidate["history"].append(row)
        candidate["step"] = self.step + 1
        candidate["exposure"][name] += 1
        candidate["sampler"] = next_member(self.config, self.control, candidate["step"])[1] \
            if candidate["step"] < self.config["max_steps"] else \
            dict(exhausted=True, completed_updates=candidate["step"], policy=POLICY)
        validate_progress(candidate, self.identity, self.control)
        self.history.append(row)
        self.step += 1
        self.dirty = False
        return deepcopy(row)

    @contextmanager
    def rng_scope(self):
        old = torch.get_rng_state()
        other = torch.mps.get_rng_state() if self.device == "mps" else None
        torch.set_rng_state(self.cpu_rng)
        if other is not None:
            torch.mps.set_rng_state(self.mps_rng)
        try:
            yield
        finally:
            self.cpu_rng = torch.get_rng_state().clone()
            torch.set_rng_state(old)
            if other is not None:
                self.mps_rng = torch.mps.get_rng_state().cpu().clone()
                torch.mps.set_rng_state(other)

    @torch.no_grad()
    def predict(self, image):
        self._clean()
        x = torch.as_tensor(image)
        require(x.device.type == "cpu" and x.dtype == torch.float32 and
            x.shape == (1, *self.config["tensor_shape"]) and torch.isfinite(x).all() and
            x.min() >= 0 and x.max() <= 1, "Invalid invented image")
        require(digest(inputs.cache.encode(x.numpy())) in
                {row["image"] for row in self.control["member_sha256"].values()},
                "Image is outside the bound invented input inventory")
        with self.rng_scope():
            self.model.eval()
            p = self.model(x[None].to(self.device)).softmax(1)[0].cpu().numpy()
        require(p.shape == (3, *self.config["tensor_shape"]) and np.isfinite(p).all() and
                np.allclose(p.sum(0), 1, atol=1e-5, rtol=0), "Invalid prediction")
        return p

    def evaluate(self, provider):
        self._clean()
        self._provider(provider)
        require(not self.evaluations or self.evaluations[-1]["step"] < self.step,
                "Duplicate/out-of-order evaluation")
        rows = []
        for role in ("train", "validation"):
            for name in self.control[role]:
                batch = provider.get(name, role=role, operation="evaluator")
                require(type(batch) is inputs.Batch, "Unsealed evaluation batch")
                x, y = batch.checked(self.identity["inputs_sha256"], "evaluator", name)
                p = self.predict(x)
                metrics = scoring.score(p.argmax(0).astype(np.uint8), (y > 0).astype(np.uint8),
                    (y == 2).astype(np.uint8), target_state="positive" if (y == 2).any() else "verified_negative")
                rows.append(dict(study_id=name, protected_role=role, **metrics))
        e = dict(step=self.step, scope="tensor_diagnostics_not_original_native_truth",
                 cases=rows, aggregate=scoring.aggregates(rows))
        prospective = progress(self)
        prospective["evaluations"].append(e)
        validate_progress(prospective, self.identity, self.control)
        self.evaluations.append(e)
        return deepcopy(e)


def progress(s):
    return dict(schema_version="segmenter-pretrained-progress-1", step=s.step, history=deepcopy(s.history),
        evaluations=deepcopy(s.evaluations), primary_checkpoint="terminal",
        exposure={n: sum(r["member_id"] == n for r in s.history) for n in s.control["train"]},
        sampler=next_member(s.config, s.control, s.step)[1] if s.step < s.config["max_steps"] else
            dict(exhausted=True, completed_updates=s.step, policy=POLICY))


def validate_progress(p, identity, control):
    require(type(p) is dict and p.get("schema_version") == "segmenter-pretrained-progress-1",
            "Wrong pretrained progress")
    mechanical = deepcopy(p) | {"schema_version": "segmenter-v5-training-progress-1"}
    i = deepcopy(identity) | {"config": _recipe(identity["config"])}
    baseline.validate_progress(mechanical, i, control)
    require(all(type(v) is int for v in p["exposure"].values()) and
            all(type(row["completed_step"]) is int and type(row["learning_rate"]) is float
                for row in p["history"]), "Progress integer/rate types")


def _state(s):
    return numerical.cpu_tree(dict(schema_version="segmenter-pretrained-state-1",
        identity_sha256=digest(canonical(s.identity)), step=s.step, model=s.model.state_dict(),
        optimizer=s.optimizer.state_dict(), cpu_rng=s.cpu_rng, mps_rng=s.mps_rng))


def payload(s):
    s._clean()
    p = progress(s)
    validate_progress(p, s.identity, s.control)
    buf = BytesIO()
    torch.save(_state(s), buf)
    files = deepcopy(s.controls) | {"identity.json": canonical(s.identity),
                                   "progress.json": canonical(p), "state.pt": buf.getvalue()}
    validate_payload(files, s.identity)
    return files


def _cpu_tensor(t, shape, dtype):
    return type(t) is torch.Tensor and t.device.type == "cpu" and t.shape == shape and t.dtype == dtype


def decode(files, identity):
    validate_identity(identity)
    require(type(files) is dict and set(files) == set(CONTROLS) | {"identity.json", "progress.json", "state.pt"}
            and all(type(v) is bytes for v in files.values()), "Wrong pretrained checkpoint inventory")
    require(len(files["identity.json"]) <= 1024**2 and len(files["state.pt"]) <= 64 * 1024**2 and
            sum(map(len, files.values())) <= 80 * 1024**2 and files["identity.json"] == canonical(identity),
            "Checkpoint identity/byte envelope")
    controls = {n: files[n] for n in CONTROLS}
    control = validate_controls(identity, controls)
    p = _json(files["progress.json"], 4 * 1024**2)
    validate_progress(p, identity, control)
    state = torch.load(BytesIO(files["state.pt"]), weights_only=True, map_location="cpu")
    _fields(state, ("schema_version", "identity_sha256", "step", "model", "optimizer", "cpu_rng", "mps_rng"),
            "Pretrained state inventory")
    require(state["schema_version"] == "segmenter-pretrained-state-1" and
            state["identity_sha256"] == digest(canonical(identity)) and type(state["step"]) is int and
            state["step"] == p["step"] and numerical.finite(state), "Changed state identity/finite/step")
    s = Session.__new__(Session)
    s._setup(identity, controls)
    expected = s.model.state_dict()
    require(type(state["model"]) is dict and set(state["model"]) == set(expected) and
            all(_cpu_tensor(state["model"][n], v.shape, v.dtype) for n, v in expected.items()),
            "Incomplete pretrained model/head")
    if state["step"] == 0:
        require(initializer.values.state_rows(state["model"]) == _json(controls["initialization.json"])["model"],
                "Step0 no longer matches initialized backbone/fresh head")
    opt, standard = state["optimizer"], s.optimizer.state_dict()
    require(type(opt) is dict and set(opt) == set(standard) and opt["param_groups"] == standard["param_groups"],
            "Changed optimizer recipe/groups")
    ids = standard["param_groups"][0]["params"]
    require(type(opt["state"]) is dict and set(opt["state"]) == (set(ids) if state["step"] else set()),
            "Incomplete optimizer state")
    for index, param in zip(ids, s.model.parameters()):
        if state["step"]:
            row = opt["state"][index]
            _fields(row, ("step", "exp_avg", "exp_avg_sq"), "AdamW state fields")
            require(_cpu_tensor(row["step"], torch.Size([]), torch.float32) and
                row["step"].item() == state["step"] and
                all(_cpu_tensor(row[k], param.shape, param.dtype) for k in ("exp_avg", "exp_avg_sq")) and
                (row["exp_avg_sq"] >= 0).all(), "Mixed AdamW steps/moments")
    require(_cpu_tensor(state["cpu_rng"], torch.get_rng_state().shape, torch.uint8), "Invalid CPU RNG")
    torch.Generator().set_state(state["cpu_rng"])
    mr = state["mps_rng"]
    require((identity["device"] == "cpu" and mr is None) or
            (identity["device"] == "mps" and type(mr) is torch.Tensor and mr.device.type == "cpu" and
             mr.dtype == torch.uint8 and mr.ndim == 1 and 0 < mr.numel() <= 4096), "Invalid native RNG")
    s.model.load_state_dict(state["model"], strict=True)
    s.optimizer.load_state_dict(opt)
    s.step, s.history, s.evaluations = state["step"], p["history"], p["evaluations"]
    s.cpu_rng, s.mps_rng = state["cpu_rng"].clone(), None if mr is None else mr.clone()
    return s


def validate_payload(files, identity):
    s = decode(files, identity)
    return dict(task=TASK, step=s.step, identity_sha256=digest(canonical(identity)),
        weights_sha256=numerical.state_hash(s.model.state_dict()), progress_sha256=digest(files["progress.json"]),
        source_sha256=_json(s.controls["source.json"])["source_sha256"],
        initialization_sha256=identity["initialization_sha256"], acceptance_sha256=identity["acceptance_sha256"],
        members={n: dict(bytes=len(v), sha256=digest(v)) for n, v in files.items()})


def restore_payload(files, identity):
    s = decode(files, identity)
    if identity["device"] == "mps":
        saved = numerical.cpu_tree(s.optimizer.state_dict())
        rng = s.mps_rng.clone()
        s._activate("mps")
        require(s.mps_rng.shape == rng.shape, "Native RNG shape differs")
        s.optimizer.load_state_dict(saved)
        s.mps_rng = rng
    return s
