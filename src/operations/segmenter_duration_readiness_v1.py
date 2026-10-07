"""Exact six-transition historical readiness reconciliation; metadata only, no model API."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
from src.data.source_inventory_records import require

TRANSITIONS = {'configs/local/roots.schema.json': ['89c44a791273b043898eb04d6749e868caae11e965317b1dba2c41166afbb6cf', '883a6829c678997c98dc6f6cb4abd36f93b7437bc1e5c7f4024a635ae3862213'], 'tests/segmenter_short_fixtures.py': ['d0d666b19edc5f32d1526ed5ffd158dec14d866a83f17d29a45e9ac68221ac86', '9ded5a9697cd12951fd627b5bf41dd828cdec2caed03300423bb8c5f543c6779'], 'tests/test_segmenter_cache_qualification.py': ['dd5e21fa1da1fd57c9742e101083d42f7d9d1fdb04e404f7aef0c8f91cd2de4d', '11194829490848007bc9d1c91a1e2f8032ad4c5f0a952f70f286c6a7046c6812'], 'tests/test_segmenter_inference_transaction.py': ['a056f773a97846c4652bbd62b5f2af9dba20ca083b2320bfefb2179fc3edd85c', 'e351ed5319bbd05820b302867db5313954eee8b343be3a762e590cb99413287b'], 'tests/test_segmenter_lowrate_native.py': ['d7cab20df34eed92201c6b492b31c3cd8bb89cc22c186ec1e93f12ee435074b9', '4181cddf604a7c43bddda6d69f618e61fc07c99ef3f7e768aa59b595323c1a55'], 'tests/test_segmenter_native_score_transaction.py': ['9eedebe50ad3af5274a27d8d70b035b37c00bb2ddb9a597693c2362dd737305b', '8565c1662f11569e06ca665c72ac16673ce5b45b5f2e031ba20fde1bc1b39d2b']}
PROVENANCE = {'outputs/prowl/TEST-PORTABILITY-20261003/export-code-attempt02.json': 'be5c9740527d30f43d1033c1ab983d7cc1685f54982a4e14a48db6ad96c13cf3', 'outputs/prowl/TEST-PORTABILITY-20261003/export-fast-tests-attempt02.log': '4b634f5cf7184043e96271e1d57018761229d72ed612cad7b2a0fae46712c3f2', 'outputs/prowl/SEGMENTER-DURATION-DUR02-20261007/storage-budget-amendment.json': 'c24fef0a54d8317f1bd306281f3552f127749773738149c455ced05ddd6d796c', 'outputs/prowl/SEGMENTER-DURATION-DUR02-20261007/roots.schema.json.before': '89c44a791273b043898eb04d6749e868caae11e965317b1dba2c41166afbb6cf', 'docs/capstone/operations/TEST-PORTABILITY-RESULTS-2026-10-03.md': '83810235b0d10c502d0791f93ad47eec87f8ad98910fdd230d43571602388d51', 'tests/retained_segmenter_metadata.py': '3c9ba1a5bdb44fce602d8dfee76fed44d32b4a42c8f28f28fd0f46835fad7184', 'tests/retained_diagnostic_metadata.py': '96b112696396492c3160ab400c7d684b38d2efc5a1bcf2ada11541d0581f11d4', 'tests/fixtures/retained_segmenter_metadata_v1/CAP-EXP-013-PREPARED-20261003/request.json': 'eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9', 'tests/fixtures/retained_segmenter_metadata_v1/README.md': '9b5f188ffd460e3175c451c3a49689e416fb4e72d9d9ebd2c4edc0090beefc29', 'tests/fixtures/retained_segmenter_metadata_v1/accepted-native-baseline.json': 'f4bfcaf0dd63ff066ce8456d66b978e738e8cca8322a6c74fcce23c89b090db2', 'tests/fixtures/retained_segmenter_metadata_v1/contracts.json': 'ec341f84d69c537827f9e1677143dbc1824cba8d1fe39941b309b1d8c214948b', 'tests/fixtures/retained_segmenter_metadata_v1/manifest.json': '04731353a52fa779868e97d96708e51a17b2725c8cad2b38a8b4f96c7a9ffc45', 'tests/fixtures/retained_segmenter_metadata_v1/train.txt': 'bfc827ac52346e4636ed3a58581d5f55a9f1e80983bbfd6228c928babd519fc8', 'tests/fixtures/retained_diagnostic_metadata_v1/README.md': '1163521f9eb49b1162817558ff322ac4496ff62a53add65915fdad434c9c8151', 'tests/fixtures/retained_diagnostic_metadata_v1/contracts.json': '756ac56d6a747887b3b618e02e85acdcadd1614c2f134b7787f3f839737c9fe7', 'tests/fixtures/retained_diagnostic_metadata_v1/manifest.json': '8dc610bd0dc1c72dde259563a551020b4f9c25643e77e17250363de958abe226'}
EXPORT = 'outputs/prowl/TEST-PORTABILITY-20261003/export-code-attempt02.json'
LOG = 'outputs/prowl/TEST-PORTABILITY-20261003/export-fast-tests-attempt02.log'
BUDGET = 'outputs/prowl/SEGMENTER-DURATION-DUR02-20261007/storage-budget-amendment.json'
OLD_SCHEMA = 'outputs/prowl/SEGMENTER-DURATION-DUR02-20261007/roots.schema.json.before'
SCHEMA = "configs/local/roots.schema.json"
PRODUCING_PROVENANCE = {n:h for n,h in PROVENANCE.items() if not n.startswith("outputs/")}


def read_pinned(root, name, expected):
    """Bounded metadata/source read. No caller-selected patient, cache or checkpoint path."""
    root = Path(root)
    path = root/name
    require(root.is_absolute() and path.resolve(strict=True) == path, "Unsafe readiness provenance path")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 4*1024**2,
                "Unsafe readiness provenance type/size")
        raw = stream.read(4*1024**2+1)
    require(len(raw) <= 4*1024**2 and hashlib.sha256(raw).hexdigest() == expected,
            "Readiness provenance/source hash differs: " + name)
    return raw


def verify_provenance(root, current):
    require(all(current.get(n) == h for n,h in PRODUCING_PROVENANCE.items()),
            "Missing pinned portable fixture/dependency closure")
    raw = {n:read_pinned(root,n,h) for n,h in PROVENANCE.items()}
    rows = json.loads(raw[EXPORT])
    require(type(rows) is list and all(type(v) is dict and set(v) == {"path","sha256"} for v in rows)
            and len({v["path"] for v in rows}) == len(rows), "Malformed successful export manifest")
    exported = {v["path"]:v["sha256"] for v in rows}
    require(all(exported.get(n) == after for n,(_,after) in TRANSITIONS.items() if n.startswith("tests/")),
            "Portable test transition not in successful export")
    require(b"2933 passed, 8 deselected" in raw[LOG], "Successful export qualification absent")
    a = json.loads(raw[BUDGET])
    require(a["author"] == "Quinton Evans" and a["instruction"] == "Approve the 26 GiB proposal"
            and a["budget_bytes"] == 26*1024**3 and a["maximum_added_backup_bytes"] == 8*1024**3
            and a["minimum_free_bytes"] == 100*1024**3 and a["preserve_all_evidence"] is True
            and a["paths"][SCHEMA] == dict(zip(("before_sha256","after_sha256"),TRANSITIONS[SCHEMA])),
            "Storage amendment provenance differs")
    prior = json.loads(raw[OLD_SCHEMA]); expected = deepcopy(prior)
    props = expected["$defs"]["backup"]["properties"]
    require(props["cap_bytes"] == {"const":20*1024**3}, "Historical schema cap differs")
    props["cap_bytes"] = {"enum":[20*1024**3,26*1024**3]}
    require(json.loads(read_pinned(root,SCHEMA,TRANSITIONS[SCHEMA][1])) == expected,
            "Schema amendment changed more than exact allowance")
    for folder in ("retained_segmenter_metadata_v1","retained_diagnostic_metadata_v1"):
        base = "tests/fixtures/"+folder+"/"
        m = json.loads(raw[base+"manifest.json"])
        require(m["origin"] == "retained_real_diagnostic_metadata_not_synthetic"
                and m["execution_authority"] is False and m["original_arrays_included"] is False
                and m["model_or_cache_payloads_included"] is False, "Fixture domain/authority changed")
        for name,entry in m["files"].items():
            require(base+name in raw and len(raw[base+name]) == entry["bytes"]
                    and hashlib.sha256(raw[base+name]).hexdigest() == entry["sha256"],
                    "Fixture dependency identity differs")
    return dict(provenance_sha256=deepcopy(PROVENANCE),model_forwards=0,optimizer_calls=0)


def reconcile(root, current, cpu, native):
    require(type(current) is dict and current and all(type(n) is str and type(h) is str
            and len(h)==64 and all(c in "0123456789abcdef" for c in h) for n,h in current.items()),
            "Malformed current source pins")
    require(cpu["state"] == "qualified" and cpu["gate"]["passed"] is True
            and native["state"] == "qualified_native_mechanics_not_real_training"
            and native["producer"]["state"] == "passed" and native["recovery"]["state"] == "passed",
            "Frozen numerical qualification missing")
    cp,mp = cpu["source_pins"],native["source_pins"]
    require(type(cp) is dict and type(mp) is dict and cp and mp
            and all(mp[n] == cp[n] for n in set(cp)&set(mp)), "Inconsistent CPU/native origin pins")
    fixed = cp|mp
    require(set(TRANSITIONS) <= set(fixed), "Missing historical transition origin")
    for n,h in fixed.items():
        before,after = TRANSITIONS.get(n,(h,h))
        require(h == before and current.get(n) == after, "Frozen numerical source closure differs: "+n)
        read_pinned(root,n,after)
    proof = verify_provenance(root,current)
    return dict(state="exact_historical_readiness_reconciled",historical_entries=len(fixed),
                accepted_transitions=deepcopy(TRANSITIONS),**proof)
