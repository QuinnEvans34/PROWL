"""Directory-only behavior and hostile-directory checks use synthetic bytes only."""
import io
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.stunet_audit.inventory_external_zip import SplitReader, inventory


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def parts(self, entries, modify=None):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            for name, data in entries:
                z.writestr(name, data)
        data = bytearray(b.getvalue())
        if modify:
            modify(data)
        split = len(data) // 2
        paths = [self.root / "part.001", self.root / "part.002"]
        paths[0].write_bytes(data[:split])
        paths[1].write_bytes(data[split:])
        return paths

    def test_split_inventory_never_opens_any_member(self):
        parts = self.parts([("images/D_1_image.nii.gz", b"synthetic-not-a-CT"),
                            ("README.md", b"synthetic provenance")])
        with patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("Member opened")):
            result = inventory(parts)
        self.assertEqual(result["declared_members"], 2)
        self.assertEqual(result["nonclinical_file_candidates"], ["README.md"])
        self.assertEqual(result["clinical_payloads_opened"], 0)
        self.assertFalse(result["member_crc_verified"])

    def test_cross_part_seek_and_read(self):
        paths = self.parts([("file", b"synthetic")])
        expected = b"".join(p.read_bytes() for p in paths)
        with SplitReader(paths) as r:
            r.seek(paths[0].stat().st_size - 3)
            self.assertEqual(r.read(8), expected[r.tell() - 8:r.tell()])
            r.seek(-4, io.SEEK_END)
            self.assertEqual(r.read(), expected[-4:])
            r.seek(100, io.SEEK_END)
            self.assertEqual(r.read(4), b"")

    def test_traversal_rejected(self):
        for name in ["../bad", "/absolute", "C:/bad", "dir\\bad"]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    inventory(self.parts([(name, b"x")]))

    def test_duplicate_rejected(self):
        with self.assertWarns(UserWarning):
            parts = self.parts([("file", b"a"), ("file", b"b")])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            inventory(parts)

    def test_symlink_rejected(self):
        item = zipfile.ZipInfo("link")
        item.create_system = 3
        item.external_attr = 0o120777 << 16
        with self.assertRaisesRegex(ValueError, "symlink"):
            inventory(self.parts([(item, b"target")]))

    def test_directory_size_guard_precedes_zipfile(self):
        def modify(data):
            i = data.rfind(b"PK\x05\x06")
            struct.pack_into("<L", data, i + 12, 9 * 1024**2)
        parts = self.parts([("file", b"x")], modify)
        with patch("scripts.stunet_audit.inventory_external_zip.zipfile.ZipFile",
                   side_effect=AssertionError("Unbounded allocation")):
            with self.assertRaisesRegex(ValueError, "size gate"):
                inventory(parts)

    def test_true_multidisk_rejected(self):
        def modify(data):
            struct.pack_into("<H", data, data.rfind(b"PK\x05\x06") + 4, 1)
        with self.assertRaisesRegex(ValueError, "multi-disk"):
            inventory(self.parts([("file", b"x")], modify))

    def test_metadata_reader_caps_unbounded_read(self):
        p = self.root / "sparse"
        with p.open("wb") as f:
            f.truncate(9 * 1024**2)
        with SplitReader([p]) as r:
            with self.assertRaisesRegex(ValueError, "8 MiB"):
                r.read()

    def test_truncated_archive_rejected(self):
        parts = self.parts([("file", b"x")])
        parts[-1].write_bytes(parts[-1].read_bytes()[:-10])
        with self.assertRaises(ValueError):
            inventory(parts)

    def test_embedded_null_is_not_silently_truncated(self):
        def modify(data):
            data[:] = data.replace(b"badXname", b"bad\x00name")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            inventory(self.parts([("badXname", b"x")], modify))

    def test_zip64_directory_across_split_parts(self):
        def modify(data):
            i = data.rfind(b"PK\x05\x06")
            end = bytearray(data[i:])
            _, _, _, on_disk, total, size, offset, _ = struct.unpack("<4s4H2LH", end)
            record = struct.pack("<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45,
                                 0, 0, on_disk, total, size, offset)
            locator = struct.pack("<4sLQL", b"PK\x06\x07", 0, i, 1)
            struct.pack_into("<L", end, 16, 0xFFFFFFFF)
            data[:] = data[:i] + record + locator + end
        result = inventory(self.parts([("README.md", b"synthetic")], modify))
        self.assertEqual(result["declared_members"], 1)
        self.assertEqual(result["member_payloads_opened"], 0)

    def test_declared_expansion_bomb_rejected_without_reading(self):
        def modify(data):
            central = data.find(b"PK\x01\x02")
            struct.pack_into("<L", data, central + 24, 3 * 1024**3)
        parts = self.parts([("file", b"x")], modify)
        with patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("Member opened")):
            with self.assertRaisesRegex(ValueError, "Expanded-size"):
                inventory(parts)


if __name__ == "__main__":
    unittest.main()
