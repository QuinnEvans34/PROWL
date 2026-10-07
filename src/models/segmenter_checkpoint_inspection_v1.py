"""SUP-02A: invented-file metadata only; no actual-file or training switch.

Hashing reads the whole invented file for identity. Subsequent archive/decoder
reads exclude storage payloads and explicitly account for virtual zero bytes.
"""
from collections import OrderedDict
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time
import zipfile


DOMAIN = "invented_serialized_checkpoint"
CONTROL_VERSION = "segmenter-checkpoint-inspection-control-1"
REPORT_VERSION = "segmenter-checkpoint-inspection-report-1"
ACTUAL_CANDIDATE_SHA = "2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3"
POLL_SECONDS = 0.05


class Refusal(ValueError):
    """A bounded refusal reason, never serialized source content."""


def _require(ok, reason):
    if not ok:
        raise Refusal(reason)


def architecture():
    return dict(in_channels=1, out_channels=32, init_filters=16, norm="group",
                num_groups=8, blocks_down=[1, 2, 2, 4], blocks_up=[1, 1, 1],
                dropout_prob=0)


def expected_signature():
    """Reviewed complete signature, without model construction or tensor access."""
    shapes = {"convInit.conv.weight": [16, 1, 3, 3, 3]}

    def block(prefix, channels):
        for n in (1, 2):
            for suffix in ("weight", "bias"):
                shapes[f"{prefix}.norm{n}.{suffix}"] = [channels]
            shapes[f"{prefix}.conv{n}.conv.weight"] = [channels, channels, 3, 3, 3]

    for level, (channels, count) in enumerate(zip((16, 32, 64, 128), (1, 2, 2, 4))):
        if level:
            shapes[f"down_layers.{level}.0.conv.weight"] = [channels, channels // 2, 3, 3, 3]
        for index in range(1, count + 1):
            block(f"down_layers.{level}.{index}", channels)
    for level, channels in enumerate((64, 32, 16)):
        block(f"up_layers.{level}.0", channels)
        shapes[f"up_samples.{level}.0.conv.weight"] = [channels, channels * 2, 1, 1, 1]
    shapes.update({"conv_final.0.weight": [16], "conv_final.0.bias": [16],
                   "conv_final.2.conv.weight": [32, 16, 1, 1, 1],
                   "conv_final.2.conv.bias": [32]})
    return {k: dict(shape=shapes[k], dtype="torch.float32") for k in sorted(shapes)}


def limits():
    return dict(max_file_bytes=64 * 1024**2, max_metadata_read_bytes=8 * 1024**2,
                max_directory_bytes=1024**2, max_pickle_bytes=1024**2,
                max_members=4096, max_storages=4096, max_storage_bytes=128 * 1024**2,
                max_model_tensors=1024, max_model_bytes=64 * 1024**2,
                max_text_bytes=512, max_depth=16, max_items=32768,
                max_control_bytes=1024**2, max_report_bytes=1024**2,
                max_worker_seconds=60, max_worker_rss_bytes=3 * 1024**3)


def _fields(value, fields, reason):
    _require(type(value) is dict and set(value) == set(fields), reason)


def _walk_json(value, depth=0, count=None):
    count = [0] if count is None else count
    count[0] += 1
    _require(depth <= 16 and count[0] <= 32768, "json_structure_limit")
    if type(value) is dict:
        for k, v in value.items():
            _require(type(k) is str, "json_key_type")
            _walk_json(k, depth + 1, count)
            _walk_json(v, depth + 1, count)
    elif type(value) is list:
        for v in value:
            _walk_json(v, depth + 1, count)
    elif type(value) is str:
        _require(len(value) <= 1024**2, "json_text_limit")
    elif type(value) is float:
        _require(math.isfinite(value), "nonfinite_json")
    else:
        _require(value is None or type(value) in (int, bool), "json_value_type")


def _json_bytes(value):
    _walk_json(value)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    _require(len(raw) <= 1024**2, "json_byte_limit")
    return raw


def control_sha256(value):
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _sha(value):
    _require(type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None,
             "invalid_sha256")


def _text(value, cap):
    _require(type(value) is str and value and all(ord(c) >= 32 for c in value),
             "invalid_text")
    _require(len(value.encode("utf-8")) <= cap, "text_limit")


def _validate_control(path, control, pin):
    _sha(pin)
    raw = _json_bytes(control)
    _require(hashlib.sha256(raw).hexdigest() == pin, "control_pin_mismatch")
    _fields(control, ("schema_version", "evidence_domain", "source", "architecture",
                      "expected_signature", "namespace", "wrapper", "limits"),
            "control_fields")
    _require(control["schema_version"] == CONTROL_VERSION, "control_version")
    _require(control["evidence_domain"] == DOMAIN, "actual_domain_refused")
    bounds = control["limits"]
    _fields(bounds, limits(), "limit_fields")
    for k, maximum in limits().items():
        v = bounds[k]
        types = (int, float) if k == "max_worker_seconds" else (int,)
        _require(type(v) in types and math.isfinite(v) and 0 < v <= maximum,
                 "invalid_limit")
    _require(bounds["max_report_bytes"] >= 2048 and bounds["max_worker_seconds"] >= .05,
             "invalid_limit")
    _require(len(raw) <= bounds["max_control_bytes"], "control_byte_limit")
    _require(control["architecture"] == architecture() and
             _json_bytes(control["architecture"]) == _json_bytes(architecture()),
             "architecture_mismatch")
    _require(control["expected_signature"] == expected_signature() and
             _json_bytes(control["expected_signature"]) == _json_bytes(expected_signature()),
             "incomplete_expected_signature")
    _require(control["namespace"] in ("identity", "uniform_module"), "namespace_policy")
    _require(control["wrapper"] == "net_optimizer_scheduler_epoch", "wrapper_policy")
    source = control["source"]
    _fields(source, ("root", "path", "bytes", "sha256"), "source_fields")
    _sha(source["sha256"])
    _require(source["sha256"] != ACTUAL_CANDIDATE_SHA, "actual_candidate_refused")
    for field in ("root", "path"):
        _text(source[field], bounds["max_text_bytes"])
        p = Path(source[field])
        _require(p.is_absolute() and str(p) == source[field] and
                 not any(part in (".", "..") for part in source[field].split("/")),
                 "unsafe_source_path")
    root, target = Path(source["root"]), Path(source["path"])
    temporary = Path(tempfile.gettempdir()).resolve()
    _require(root != temporary and temporary in root.parents and
             root.name.startswith("prowl-invented-checkpoint-"), "non_test_root_refused")
    _require(type(path) in (str, type(Path())), "path_type")
    _require(str(path) == str(target) and target.parent == root and
             re.fullmatch(r"invented-[A-Za-z0-9_.-]+\.pth", target.name) is not None,
             "source_path_mismatch")
    _require(type(source["bytes"]) is int and
             0 < source["bytes"] <= bounds["max_file_bytes"], "file_byte_limit")
    logical = sum(math.prod(v["shape"]) * 4 for v in expected_signature().values())
    _require(len(expected_signature()) <= bounds["max_model_tensors"], "model_tensor_limit")
    _require(logical <= bounds["max_model_bytes"], "model_byte_limit")
    return json.loads(raw)


def _identity(info):
    return tuple(getattr(info, k) for k in
                 ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns",
                  "st_nlink"))


def _no_symlinks(path):
    for ancestor in reversed((path, *path.parents)):
        _require(not stat.S_ISLNK(os.lstat(ancestor).st_mode), "symlink_refused")


class _Source:
    def __init__(self, control):
        self.control = control
        self.path = Path(control["source"]["path"])
        self.root = self.path.parent
        self.fd = None
        self.hash_bytes = self.metadata_bytes = self.virtual_bytes = self.requested = 0
        self.metadata_ranges = []
        self.storage_spans = []
        self.root_identity = None

    def __enter__(self):
        _no_symlinks(self.path)
        # Walk ancestors through directory descriptors, not a followable full-path open.
        directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in self.root.parts[1:]:
                following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                    dir_fd=directory)
                os.close(directory)
                directory = following
            root_info = os.fstat(directory)
            _require(root_info.st_uid == os.getuid() and
                     stat.S_IMODE(root_info.st_mode) == 0o700, "non_private_test_root")
            self.root_identity = (root_info.st_dev, root_info.st_ino)
            fd = os.open(self.path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory)
            try:
                info = os.fstat(fd)
                _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                         "non_regular_or_hardlinked_source")
                _require(info.st_size == self.control["source"]["bytes"], "file_size_mismatch")
                self.initial = _identity(info)
                self.fd = fd
            except BaseException:
                os.close(fd)
                raise
        finally:
            os.close(directory)
        try:
            self.check()
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise
        return self

    def __exit__(self, *args):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def check(self):
        _no_symlinks(self.path)
        root = os.stat(self.root, follow_symlinks=False)
        _require((root.st_dev, root.st_ino) == self.root_identity, "root_replaced")
        _require(root.st_uid == os.getuid() and stat.S_IMODE(root.st_mode) == 0o700,
                 "non_private_test_root")
        _require(_identity(os.fstat(self.fd)) == self.initial and
                 _identity(os.stat(self.path, follow_symlinks=False)) == self.initial,
                 "source_mutated_or_replaced")

    def _pread(self, start, count, *, hashing=False):
        size = self.control["source"]["bytes"]
        _require(type(start) is int and type(count) is int and
                 start >= 0 and count >= 0 and start + count <= size, "read_out_of_file")
        cap = size + self.control["limits"]["max_metadata_read_bytes"]
        _require(self.requested + count <= cap, "aggregate_read_limit")
        if not hashing:
            _require(self.requested - self.hash_bytes + count <=
                     self.control["limits"]["max_metadata_read_bytes"], "metadata_read_limit")
        self.check()
        data = os.pread(self.fd, count, start)
        self.requested += count
        _require(len(data) == count, "short_read")
        if hashing:
            self.hash_bytes += count
        else:
            _require(len(self.metadata_ranges) < self.control["limits"]["max_items"],
                     "read_request_limit")
            self.metadata_ranges.append((start, start + count))
            self.metadata_bytes += count
        self.check()
        return data

    def hash(self):
        digest = hashlib.sha256()
        size = self.control["source"]["bytes"]
        for start in range(0, size, 1024**2):
            digest.update(self._pread(start, min(1024**2, size - start), hashing=True))
        observed = digest.hexdigest()
        _require(observed == self.control["source"]["sha256"], "file_hash_mismatch")
        return observed

    def metadata(self, start, count):
        """Virtual bytes count toward the same budget; no source storage read."""
        end = start + count
        _require(self.requested - self.hash_bytes + count <=
                 self.control["limits"]["max_metadata_read_bytes"], "metadata_read_limit")
        self.check()
        parts, cursor = [], start
        for low, high in self.storage_spans:
            low, high = max(low, start), min(high, end)
            if low >= high:
                continue
            if cursor < low:
                parts.append(self._pread(cursor, low - cursor))
            zeros = high - low
            parts.append(bytes(zeros))
            self.virtual_bytes += zeros
            self.requested += zeros
            cursor = high
        if cursor < end:
            parts.append(self._pread(cursor, end - cursor))
        self.check()
        return b"".join(parts)

    def evidence(self):
        overlap = sum(max(0, min(b, y) - max(a, x))
                      for a, b in self.metadata_ranges for x, y in self.storage_spans)
        return dict(hash_bytes=self.hash_bytes, metadata_source_bytes=self.metadata_bytes,
                    virtual_zero_bytes=self.virtual_bytes, aggregate_requested_bytes=self.requested,
                    metadata_storage_source_bytes=overlap)


class _View(io.RawIOBase):
    """No name/fileno/mmap or independent file reader is exposed to the decoder."""
    def __init__(self, source):
        self._source = source
        self._offset = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self._offset

    def seek(self, offset, whence=0):
        size = self._source.control["source"]["bytes"]
        _require(type(offset) is int and whence in (0, 1, 2), "invalid_seek")
        position = offset + (0 if whence == 0 else self._offset if whence == 1 else size)
        _require(0 <= position <= size, "seek_out_of_file")
        self._offset = position
        return position

    def read(self, size=-1):
        _require(type(size) is int and size >= -1, "invalid_read")
        remaining = self._source.control["source"]["bytes"] - self._offset
        count = remaining if size == -1 else min(size, remaining)
        data = self._source.metadata(self._offset, count)
        self._offset += count
        return data

    def readinto(self, target):
        data = self.read(len(target))
        target[:len(data)] = data
        return len(data)


def _archive(source):
    bounds = source.control["limits"]
    size = source.control["source"]["bytes"]
    _require(size >= 22, "legacy_or_truncated_format")
    footer = struct.unpack("<4s4H2IH", source.metadata(size - 22, 22))
    _require(footer[0] == b"PK\x05\x06" and footer[-1] == 0, "zip_footer_or_comment")
    _, disk, directory_disk, count_disk, count, directory_bytes, directory_offset, _ = footer
    _require(disk == directory_disk == 0 and count_disk == count, "multivolume_zip")
    index_end = size - 22
    if size >= 42:
        locator = source.metadata(size - 42, 20)
        if locator[:4] == b"PK\x06\x07":
            _, zip_disk, zip_offset, disks = struct.unpack("<4sIQI", locator)
            _require(zip_disk == 0 and disks == 1 and zip_offset + 56 == size - 42,
                     "invalid_zip64_locator")
            z64 = struct.unpack("<4sQ2H2I4Q", source.metadata(zip_offset, 56))
            _require(z64[0] == b"PK\x06\x06" and z64[1] == 44 and
                     z64[4] == z64[5] == 0 and z64[6] == z64[7],
                     "invalid_zip64_footer")
            _require((count == z64[7] or count == 65535) and
                     (directory_bytes == z64[8] or directory_bytes == 2**32 - 1) and
                     (directory_offset == z64[9] or directory_offset == 2**32 - 1),
                     "zip64_footer_disagreement")
            count, directory_bytes, directory_offset = z64[7:10]
            index_end = zip_offset
    _require(0 < count <= bounds["max_members"], "member_count_limit")
    _require(0 < directory_bytes <= bounds["max_directory_bytes"], "directory_byte_limit")
    _require(directory_offset > 0 and directory_offset + directory_bytes == index_end,
             "directory_out_of_file")
    _require(source.metadata(0, 4) == b"PK\x03\x04", "legacy_format_refused")
    with zipfile.ZipFile(_View(source), "r") as archive:
        items = archive.infolist()
    _require(len(items) == count, "directory_count_disagreement")
    names, rows, storages, storage_bytes = set(), [], {}, 0
    root = None
    preceding_end = 0
    for item in sorted(items, key=lambda i: i.header_offset):
        name = item.filename
        _text(name, bounds["max_text_bytes"])
        _require("\\" not in name and ":" not in name and not name.startswith("/") and
                 all(p not in ("", ".", "..") for p in name.split("/")), "unsafe_member_name")
        _require(name not in names, "duplicate_member")
        names.add(name)
        prefix, separator, relative = name.partition("/")
        root = prefix if root is None else root
        _require(separator and prefix == root, "mixed_archive_root")
        is_storage = re.fullmatch(r"data/(0|[1-9][0-9]*)", relative) is not None
        maxima = {"data.pkl": bounds["max_pickle_bytes"], "byteorder": 16, "version": 16,
                  ".format_version": 16, ".storage_alignment": 16, ".data/serialization_id": 64}
        _require(is_storage or relative in maxima, "unknown_archive_member")
        _require(item.compress_type == zipfile.ZIP_STORED and
                 item.compress_size == item.file_size, "compressed_member_refused")
        _require(item.flag_bits & ~0x808 == 0, "encrypted_or_unsupported_flags")
        mode = item.external_attr >> 16
        _require(not stat.S_ISLNK(mode), "archive_symlink_refused")
        _require(is_storage or item.file_size <= maxima[relative], "metadata_member_byte_limit")
        _require(item.header_offset >= preceding_end and
                 item.header_offset + 30 <= directory_offset, "overlapping_or_bad_header")
        local = struct.unpack("<4s5H3I2H", source.metadata(item.header_offset, 30))
        _require(local[0] == b"PK\x03\x04" and local[2] == item.flag_bits and
                 local[3] == item.compress_type, "local_header_disagreement")
        name_bytes, extra_bytes = local[-2:]
        _require(name_bytes <= bounds["max_text_bytes"] and
                 item.header_offset + 30 + name_bytes + extra_bytes <= directory_offset,
                 "local_header_byte_limit")
        encoded_name = source.metadata(item.header_offset + 30, name_bytes)
        _require(encoded_name.decode("utf-8" if item.flag_bits & 0x800 else "cp437") == name,
                 "local_name_disagreement")
        _require(local[6] in (0, item.CRC) and local[7] in (0, item.file_size) and
                 local[8] in (0, item.file_size), "local_size_disagreement")
        payload = item.header_offset + 30 + name_bytes + extra_bytes
        end = payload + item.file_size
        _require(end <= directory_offset, "payload_out_of_file")
        descriptor = 16 if item.flag_bits & 8 else 0
        _require(end + descriptor <= directory_offset, "descriptor_out_of_file")
        if descriptor:
            desc = struct.unpack("<4s3I", source.metadata(end, descriptor))
            _require(desc == (b"PK\x07\x08", item.CRC, item.file_size, item.file_size),
                     "data_descriptor_disagreement")
        preceding_end = end + descriptor
        row = dict(name=relative, header_offset=item.header_offset,
                   payload_offset=payload, bytes=item.file_size)
        rows.append(row)
        if is_storage:
            storages[payload] = row
            storage_bytes += item.file_size
            _require(len(storages) <= bounds["max_storages"], "storage_count_limit")
            _require(storage_bytes <= bounds["max_storage_bytes"], "storage_byte_limit")
    _require(root + "/data.pkl" in names and root + "/version" in names, "missing_metadata_member")
    _require(len(storages) > 0, "missing_storage_members")
    source.storage_spans = sorted((offset, offset + row["bytes"]) for offset, row in storages.items())
    _require(source.evidence()["metadata_storage_source_bytes"] == 0, "archive_storage_read_refused")
    return dict(members=rows, storage_count=len(storages), declared_storage_bytes=storage_bytes), storages


def _inventory(blob, control, storages, torch, fake_type):
    _fields(blob, ("net", "optimizer", "scheduler", "epoch"), "wrapper_mismatch")
    _require(type(blob["net"]) in (dict, OrderedDict), "model_mapping_type")
    _require(type(blob["optimizer"]) is dict and type(blob["scheduler"]) is dict and
             type(blob["epoch"]) is int and 0 <= blob["epoch"] <= 2**53, "auxiliary_wrapper_type")
    bounds = control["limits"]
    visited, aliases, used_storages = [0], {}, set()
    dtypes = {torch.float32, torch.float64, torch.float16, torch.bfloat16,
              torch.int64, torch.int32, torch.int16, torch.int8, torch.uint8, torch.bool}

    def tensor(value, path):
        _require(type(value) is fake_type and value.layout == torch.strided and
                 not value.is_quantized and value.dtype in dtypes, "unsupported_tensor_type_or_layout")
        shape, stride = list(value.shape), list(value.stride())
        _require(len(shape) <= 8 and all(type(n) is int and n >= 0 for n in shape) and
                 all(type(n) is int and n >= 0 for n in stride), "unsupported_tensor_view")
        storage = value.untyped_storage()
        location = getattr(storage, "_fake_device", None)
        offset = getattr(storage, "_checkpoint_offset", None)
        _require(location == "cpu" and value.device.type == "cpu" and storage.device.type == "meta",
                 "non_cpu_or_materialized_storage")
        _require(type(offset) is int and offset in storages, "storage_offset_mismatch")
        member = storages[offset]
        storage_bytes = storage.nbytes()
        _require(storage_bytes == member["bytes"], "storage_size_mismatch")
        element_bytes, start = value.element_size(), value.storage_offset()
        logical = math.prod(shape) * element_bytes
        _require(logical <= bounds["max_model_bytes"] and type(start) is int and start >= 0,
                 "logical_view_byte_limit")
        span = 0 if math.prod(shape) == 0 else 1 + sum((n - 1) * s for n, s in zip(shape, stride))
        _require((start + span) * element_bytes <= storage_bytes, "view_out_of_storage")
        _require(value.is_contiguous() and not value.requires_grad and
                 not value.is_conj() and not value.is_neg(), "unsupported_tensor_view")
        used_storages.add(offset)
        aliases.setdefault(member["name"], []).append(path)
        return dict(shape=shape, dtype=str(value.dtype), stride=stride, storage_offset=start,
                    logical_bytes=logical, storage_bytes=storage_bytes, source_device=location,
                    storage_file_offset=offset, storage_member=member["name"])

    def visit(value, path, depth=0):
        visited[0] += 1
        _require(depth <= bounds["max_depth"] and visited[0] <= bounds["max_items"],
                 "container_structure_limit")
        if type(value) is fake_type:
            return {"tensor": tensor(value, path)}
        if type(value) in (dict, OrderedDict):
            if type(value) is OrderedDict:
                _require(not vars(value), "container_attributes_refused")
            rows = []
            for key, v in value.items():
                _require(type(key) in (str, int) and type(key) is not bool, "container_key_type")
                if type(key) is str:
                    if key:  # state_dict version maps use an empty root-module key.
                        _text(key, bounds["max_text_bytes"])
                else:
                    _require(abs(key) <= 2**53, "primitive_integer_limit")
                rows.append({"key": key, "value": visit(v, path + "/" + str(key), depth + 1)})
            return {"mapping": rows}
        if type(value) is list:
            return {"list": [visit(v, path + "/" + str(i), depth + 1) for i, v in enumerate(value)]}
        _require(value is None or type(value) in (str, int, float, bool), "container_value_type")
        if type(value) is str:
            if value:
                _text(value, bounds["max_text_bytes"])
        elif type(value) is float:
            _require(math.isfinite(value), "nonfinite_primitive")
        elif type(value) is int:
            _require(abs(value) <= 2**53, "primitive_integer_limit")
        return {"primitive": value}

    net, normalized = blob["net"], {}
    _require(0 < len(net) <= bounds["max_model_tensors"], "model_tensor_limit")
    for key, value in net.items():
        _text(key, bounds["max_text_bytes"])
        if control["namespace"] == "uniform_module":
            _require(key.startswith("module.") and not key.startswith("module.module."),
                     "namespace_mismatch")
            key = key[len("module."):]
        else:
            _require(not key.startswith("module."), "namespace_mismatch")
        _require(key not in normalized, "namespace_collision")
        normalized[key] = value
    _require(set(normalized) == set(control["expected_signature"]), "model_key_mismatch")
    model = {}
    for key in sorted(normalized):
        value = normalized[key]
        _require(type(value) is fake_type, "unsupported_tensor_type_or_layout")
        expected = control["expected_signature"][key]
        _require(list(value.shape) == expected["shape"] and str(value.dtype) == expected["dtype"],
                 "model_shape_or_dtype_mismatch")
        model[key] = tensor(value, "net/" + key)
    _require(sum(row["logical_bytes"] for row in model.values()) <= bounds["max_model_bytes"],
             "model_byte_limit")
    auxiliary = {k: visit(blob[k], k) for k in ("optimizer", "scheduler", "epoch")}
    if type(net) is OrderedDict:
        _require(set(vars(net)) <= {"_metadata"}, "model_attributes_refused")
        if hasattr(net, "_metadata"):
            # state_dict's version map is serialized too. Inventory it, rather
            # than silently ignoring bounded data attached to OrderedDict.
            metadata = net._metadata
            _require(type(metadata) in (dict, OrderedDict), "model_metadata_type")
            if type(metadata) is OrderedDict:
                _require(not vars(metadata), "container_attributes_refused")
                metadata = dict(metadata)
            auxiliary["net_metadata"] = visit(metadata, "net_metadata")
    _require(used_storages == set(storages), "unreferenced_storage")
    return model, dict(fields=auxiliary,
                       aliases={k: sorted(v) for k, v in sorted(aliases.items()) if len(v) > 1})


def _report(reason="pending"):
    return dict(schema_version=REPORT_VERSION, status="refused", reason=reason,
                evidence_domain=DOMAIN, scope="metadata_only", execution_authority="none",
                training_eligible=False, identity_verified=False, metadata_compatible=False,
                values_audited=False, control_sha256=None, source_sha256=None, source_bytes=None,
                archive=None, model=None, auxiliary=None, io=None, worker=None)


def _inspect_local(path, control, pin):
    """Worker implementation; tests may call with invented fixtures, never a real boundary."""
    report, source = _report(), None
    try:
        control = _validate_control(path, control, pin)
        report.update(control_sha256=pin, source_bytes=control["source"]["bytes"])
        with _Source(control) as source:
            report["source_sha256"] = source.hash()
            report["identity_verified"] = True
            report["archive"], storages = _archive(source)
            import torch
            from torch._subclasses.fake_tensor import FakeTensor, FakeTensorMode
            # The caller is isolated before reaching this code. Never relax restricted loading.
            with FakeTensorMode(allow_fallback_kernels=False):
                # FakeTensorMode initializes trusted torch subsystems that themselves
                # register globals. Clear only after that initialization, before loading.
                torch.serialization.clear_safe_globals()
                _require(torch.serialization.get_safe_globals() == [], "ambient_safe_globals")
                blob = torch.load(_View(source), weights_only=True, map_location="cpu", mmap=False)
            _require(torch.serialization.get_safe_globals() == [], "safe_globals_changed")
            report["model"], report["auxiliary"] = _inventory(blob, control, storages, torch, FakeTensor)
            source.check()
            report.update(status="pass", reason="complete_metadata_match", metadata_compatible=True)
    except Refusal as error:
        report["reason"] = str(error)
    except (OSError, ValueError, RuntimeError, TypeError, AttributeError, EOFError, zipfile.BadZipFile):
        report["reason"] = "format_or_restricted_decode_refused"
    except Exception:
        report["reason"] = "restricted_decode_refused"
    finally:
        if source is not None:
            report["io"] = source.evidence()
    return report


def _sample_rss(pid):
    result = subprocess.run(["/bin/ps", "-o", "rss=", "-p", str(pid)],
                            capture_output=True, timeout=1, check=False)
    _require(result.returncode == 0 and result.stdout.strip().isdigit(), "rss_monitor_unavailable")
    return int(result.stdout.strip()) * 1024


def _stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=.2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=1)
    return process.returncode


def _worker_run(control, pin):
    bounds = control["limits"]
    result = _report()
    start, peak, process = time.monotonic(), 0, None
    stdout, stderr = bytearray(), bytearray()
    try:
        _require(os.name == "posix" and sys.platform in ("darwin", "linux"), "monitor_platform_unqualified")
        env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C",
               "TMPDIR": str(Path(tempfile.gettempdir()).resolve()), "OMP_NUM_THREADS": "1",
               "MKL_NUM_THREADS": "1", "TORCH_FORCE_WEIGHTS_ONLY_LOAD": "1"}
        process = subprocess.Popen([sys.executable, "-I", str(Path(__file__).resolve()), "--worker"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=env, start_new_session=True, close_fds=True)
        # Child waits for input: monitor availability is proven before importing torch/opening source.
        peak = _sample_rss(process.pid)
        _require(peak <= bounds["max_worker_rss_bytes"], "worker_rss_limit")
        payload = _json_bytes({"control": control, "pin": pin})
        process.stdin.write(payload)
        process.stdin.close()
        with selectors.DefaultSelector() as select:
            for stream, tag in ((process.stdout, "out"), (process.stderr, "err")):
                select.register(stream, selectors.EVENT_READ, tag)
            while select.get_map():
                _require(time.monotonic() - start <= bounds["max_worker_seconds"], "worker_time_limit")
                if process.poll() is None:
                    try:
                        peak = max(peak, _sample_rss(process.pid))
                    except Refusal:
                        _require(process.poll() is not None, "rss_monitor_unavailable")
                    _require(peak <= bounds["max_worker_rss_bytes"], "worker_rss_limit")
                for key, _ in select.select(POLL_SECONDS):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        select.unregister(key.fileobj)
                    elif key.data == "out":
                        stdout.extend(data)
                        _require(len(stdout) <= bounds["max_report_bytes"], "worker_output_limit")
                    else:
                        stderr.extend(data)
                        _require(len(stderr) <= 65536, "worker_log_limit")
        _require(process.wait(timeout=1) == 0, "worker_exit_failure")
        result = json.loads(stdout)
        _require(type(result) is dict and set(result) == set(_report()), "worker_report_schema")
        _require(result["execution_authority"] == "none" and result["training_eligible"] is False and
                 result["values_audited"] is False, "worker_report_authority")
    except Refusal as error:
        result = _report(str(error))
    except (OSError, ValueError, subprocess.SubprocessError):
        result = _report("worker_or_monitor_unavailable")
    finally:
        if process is not None:
            _stop(process)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
    own_peak = (result.get("worker") or {}).get("child_peak_rss_bytes")
    result["worker"] = dict(method="isolated_child_ps_sample", sampling_seconds=POLL_SECONDS,
                            elapsed_seconds=round(time.monotonic() - start, 6),
                            sampled_peak_rss_bytes=peak, child_peak_rss_bytes=own_peak,
                            exit_code=None if process is None else process.returncode,
                            termination_reason=None if result["status"] == "pass" else result["reason"])
    if own_peak is not None and own_peak > bounds["max_worker_rss_bytes"]:
        result.update(status="refused", reason="worker_peak_rss_limit", metadata_compatible=False)
        result["worker"]["termination_reason"] = "worker_peak_rss_limit"
    try:
        _require(len(_json_bytes(result)) <= bounds["max_report_bytes"], "report_byte_limit")
    except Refusal:
        result = _report("report_byte_limit")
    return result


def inspect_checkpoint(path, *, pinned_control, expected_control_sha256):
    """Inspect one invented temporary fixture; report has no execution authority."""
    try:
        control = _validate_control(path, pinned_control, expected_control_sha256)
    except Refusal as error:
        return _report(str(error))
    except (ValueError, TypeError, UnicodeError, OverflowError, OSError, RecursionError):
        return _report("invalid_control")
    return _worker_run(control, expected_control_sha256)


def _worker_main():
    import resource
    try:
        raw = sys.stdin.buffer.read(1024**2 + 1)
        _require(len(raw) <= 1024**2, "worker_control_byte_limit")
        inputs = json.loads(raw)
        _fields(inputs, ("control", "pin"), "worker_input_fields")
        control = inputs["control"]
        result = _inspect_local(control["source"]["path"], control, inputs["pin"])
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result["worker"] = {"child_peak_rss_bytes": peak if sys.platform == "darwin" else peak * 1024}
        maximum = control["limits"]["max_report_bytes"]
        if len(_json_bytes(result)) > maximum:
            result = _report("report_byte_limit")
        sys.stdout.buffer.write(_json_bytes(result))
    except Exception:
        sys.stdout.buffer.write(_json_bytes(_report("worker_input_or_report_refused")))


if __name__ == "__main__":
    if sys.argv[1:] != ["--worker"]:
        raise SystemExit("Invented inspection worker only; no real-file command.")
    _worker_main()
