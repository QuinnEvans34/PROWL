"""Inspect bounded ZIP directory metadata across byte-split parts; never open members.

Publisher checksum verification must precede real use. This is not a medical
image validator, extraction tool, or proof of patient independence.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import io
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import struct
import zipfile


class SplitReader(io.RawIOBase):
    """Seek through ordered parts without creating a second archive copy."""

    def __init__(self, paths: list[Path]):
        super().__init__()
        if not paths or len(set(map(str, paths))) != len(paths):
            raise ValueError("Require nonempty, distinct, explicitly ordered parts")
        self.files = []
        self.offsets = [0]
        self.position = 0
        try:
            for path in paths:
                f = path.open("rb")
                self.files.append(f)
                self.offsets.append(self.offsets[-1] + path.stat().st_size)
        except BaseException:
            self.close()
            raise
        self.size = self.offsets[-1]

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence not in (io.SEEK_SET, io.SEEK_CUR, io.SEEK_END):
            raise ValueError("Unknown seek origin")
        position = offset + (0 if whence == io.SEEK_SET else
                             self.position if whence == io.SEEK_CUR else self.size)
        if position < 0:
            raise ValueError("Negative seek")
        self.position = position
        return position

    def read(self, size=-1):
        if self.closed:
            raise ValueError("Reader closed")
        size = max(0, self.size - self.position) if size < 0 else size
        # A directory parser should never request an entire clinical archive.
        if size > 8 * 1024**2:
            raise ValueError("Metadata read exceeds 8 MiB cap")
        remaining = min(size, max(0, self.size - self.position))
        output = bytearray()
        while remaining:
            index = bisect_right(self.offsets, self.position) - 1
            count = min(remaining, self.offsets[index + 1] - self.position)
            self.files[index].seek(self.position - self.offsets[index])
            block = self.files[index].read(count)
            if len(block) != count:
                raise ValueError("Part truncated or changed during inspection")
            output.extend(block)
            self.position += count
            remaining -= count
        return bytes(output)

    def close(self):
        for f in self.files:
            f.close()
        super().close()


def check_directory_bounds(reader: SplitReader):
    """Validate EOCD sizes before zipfile allocates its central-directory buffer."""
    reader.seek(max(0, reader.size - (65535 + 22)))
    tail = reader.read()
    index = tail.rfind(b"PK\x05\x06")
    if index < 0 or index + 22 > len(tail):
        raise ValueError("ZIP end record missing")
    _, disk, cd_disk, disk_count, count, size, offset, comment = struct.unpack(
        "<4s4H2LH", tail[index:index + 22])
    if index + 22 + comment != len(tail):
        raise ValueError("ZIP end record/comment length differs")
    if disk or cd_disk:
        raise ValueError("True multi-disk ZIP needs separately qualified handling")
    eocd_offset = reader.size - len(tail) + index
    if count == 65535 or size == 0xFFFFFFFF or offset == 0xFFFFFFFF:
        if eocd_offset < 20:
            raise ValueError("ZIP64 locator missing")
        reader.seek(eocd_offset - 20)
        signature, end_disk, end_offset, disks = struct.unpack("<4sLQL", reader.read(20))
        if signature != b"PK\x06\x07" or end_disk or disks != 1:
            raise ValueError("Invalid or multi-disk ZIP64 locator")
        reader.seek(end_offset)
        raw = reader.read(56)
        if len(raw) != 56:
            raise ValueError("ZIP64 end record truncated")
        fields = struct.unpack("<4sQ2H2L4Q", raw)
        if fields[0] != b"PK\x06\x06" or fields[1] != 44 or fields[4] or fields[5]:
            raise ValueError("Unsupported ZIP64 end record")
        disk_count, count, size, offset = fields[6:10]
    if disk_count != count or count > 5000 or size > 8 * 1024**2:
        raise ValueError("Directory count/size gate failed")
    if offset + size > eocd_offset:
        raise ValueError("Directory outside archive bounds")
    return dict(declared_members=count, central_directory_bytes=size)


def inventory(paths: list[Path]):
    with SplitReader(paths) as reader:
        bounds = check_directory_bounds(reader)
        reader.seek(0)
        with zipfile.ZipFile(reader) as archive:
            members = archive.infolist()
            if len(members) != bounds["declared_members"]:
                raise ValueError("Directory member count differs")
            rows = []
            seen = set()
            expanded = 0
            for item in members:
                name = item.filename
                posix = PurePosixPath(name)
                if ("\x00" in item.orig_filename or "\\" in name or posix.is_absolute() or
                        ".." in posix.parts or PureWindowsPath(name).drive):
                    raise ValueError("Unsafe member path")
                if name in seen or stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError("Duplicate path or symlink")
                if item.flag_bits & 1:
                    raise ValueError("Encrypted member")
                seen.add(name)
                expanded += item.file_size
                if item.file_size > 2 * 1024**3 or expanded > 64 * 1024**3:
                    raise ValueError("Expanded-size cap")
                clinical = name.lower().endswith((".nii", ".nii.gz", ".dcm", ".mha", ".nrrd"))
                rows.append(dict(path=name, directory=item.is_dir(),
                                 compressed_bytes=item.compress_size, expanded_bytes=item.file_size,
                                 crc32=f"{item.CRC:08x}", compression=item.compress_type,
                                 clinical_filename=clinical))
            return dict(schema="prowl.external-zip-inventory.v1", parts=[str(p) for p in paths],
                        archive_bytes=reader.size, **bounds, members=rows,
                        expanded_bytes=expanded,
                        nonclinical_file_candidates=[r["path"] for r in rows
                            if not r["directory"] and not r["clinical_filename"]],
                        member_payloads_opened=0, clinical_payloads_opened=0,
                        member_crc_verified=False, extracted_files=0,
                        patient_independence_verified=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("parts", type=Path, nargs="+")
    args = parser.parse_args()
    result = inventory(args.parts)
    with args.output.open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "members"}))
