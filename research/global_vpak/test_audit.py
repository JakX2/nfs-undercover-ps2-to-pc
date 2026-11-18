"""Synthetic-only tests; no copyrighted game files required."""
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from audit import audit, overlap, parse_attributes, parse_gameplay, read_selected_members, string_region

def er_ts(names):
    payload = b"\x00".join(name.encode("ascii") for name in names) + b"\x00"
    padding = (-8 - len(payload)) % 4
    return b"ErtS" + struct.pack("<I", 8 + len(payload) + padding) + payload + b"\0" * padding

def fixture_gameplay(names):
    pool = er_ts(names)
    buf = bytearray(64)
    struct.pack_into("<4sIII", buf, 0, b"VPAK", 1, 64, 123)
    struct.pack_into("<IIIII", buf, 16, 0, len(pool), 0, 64, 64 + len(pool))
    return bytes(buf) + pool

def fixture_attributes(names):
    return b"VPAK" + b"\0" * 124 + er_ts(names)

def make_zip(path, members):
    with zipfile.ZipFile(path, "w") as dest:
        for name, value in members.items():
            dest.writestr(name, value)

class TestVPAK(unittest.TestCase):
    def test_string_pool(self):
        data = er_ts(["checkpoint", "race/path"])
        size, names = string_region(data, 0)
        self.assertEqual(size, len(data))
        self.assertEqual(names, ["checkpoint", "race/path"])

    def test_gameplay(self):
        info, names = parse_gameplay(fixture_gameplay(["foo", "foo", "bar"]))
        self.assertEqual(info["indexed_entries"], 1)
        self.assertEqual(info["name_occurrences"], 3)
        self.assertEqual(names, {"foo", "bar"})

    def test_bad_magic(self):
        with self.assertRaisesRegex(ValueError, "VPAK"):
            parse_gameplay(b"NOPE" + fixture_gameplay(["a"])[4:])

    def test_bad_offset(self):
        data = bytearray(fixture_gameplay(["a"]))
        struct.pack_into("<I", data, 16 + 12, 999999)
        with self.assertRaises(ValueError):
            parse_gameplay(data)

    def test_missing_erts(self):
        data = bytearray(fixture_gameplay(["a"]))
        data[64:68] = b"XXXX"
        with self.assertRaises(ValueError):
            parse_gameplay(data)

    def test_attribute_prefix(self):
        info, names = parse_attributes(fixture_attributes(["COPS", "NITROUS"]))
        self.assertEqual(info["distinct_names"], 2)
        self.assertEqual(names, {"COPS", "NITROUS"})

    def test_overlap(self):
        self.assertEqual(overlap({"a", "b"}, {"b", "c"}), {"shared": 1, "left_only": 1, "right_only": 1})

    def test_duplicate_member_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "dup.zip"
            with zipfile.ZipFile(path, "w") as dest:
                dest.writestr("root/GAMEPLAY.BIN", b"1")
                dest.writestr("other/GAMEPLAY.BIN", b"2")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read_selected_members(path)

    def test_three_way_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            paths = [directory / f"src{i}.zip" for i in range(3)]
            make_zip(paths[0], {
                "GAMEPLAY.BIN": fixture_gameplay(["a", "b", "NFS-VltEd 4.6.0.0 by nfsu360"]),
                "GAMEPLAY.BAK": fixture_gameplay(["a", "b"]),
                "ATTRIBUTES.BIN": fixture_attributes(["alpha"]),
                "ATTRIBUTES.BAK": fixture_attributes(["alpha"]),
                "FE_ATTRIB.BIN": fixture_attributes(["fe"]),
                "FE_ATTRIB.BAK": fixture_attributes(["fe"]),
            })
            for path, race in ((paths[1], ["a"]), (paths[2], ["b"])):
                make_zip(path, {
                    "GAMEPLAY.BIN": fixture_gameplay(race),
                    "ATTRIBUTES.BIN": fixture_attributes(["alpha"]),
                    "FE_ATTRIB.BIN": fixture_attributes(["fe"]),
                })
            report = audit(*paths)
            self.assertEqual(report["gameplay"]["carbon_pc/GAMEPLAY.BIN"]["editor_marker_occurrences"], 1)
            self.assertEqual(report["comparisons"]["pc_backup_vs_carbon_ps2"]["shared"], 1)
            self.assertEqual(report["comparisons"]["pc_backup_vs_carbon_ps2_FE_ATTRIB"]["shared"], 1)

if __name__ == "__main__":
    unittest.main()
