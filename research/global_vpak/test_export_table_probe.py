"""Synthetic-only regression tests for the NpxE offset/length chain."""
import struct
import unittest

from chunk_layout import parse_chunks
from export_table_probe import align8, inspect_export_entries


def chunk(tag, payload):
    size = 8 + len(payload)
    assert size % 16 == 0
    return tag + struct.pack("<I", size) + payload


def fixture(entries=None, data_size=160):
    if entries is None:
        entries = [
            (0x8E112EB7, 24, 40, 0x12345678),
            (0x8E112EB7, 32, 64, 0x87654321),
            (0x8E112EB7, 0, 96, 0),
        ]
    text = b"ErtS" + struct.pack("<I", 16) + b"name\0\0\0\0"
    data = chunk(b"NtaD", b"\0" * (data_size - 8))
    export = chunk(b"NpxE", struct.pack("<II", len(entries), 0) + b"".join(struct.pack("<4I", *e) for e in entries))
    aux = (chunk(b"sreV", b"\x11" * 8) + chunk(b"NpeD", b"\x22" * 40)
           + chunk(b"NrtS", b"\0" * 8) + data + export + chunk(b"NrtP", b"\x33" * 24))
    header = bytearray(64)
    struct.pack_into("<4sIII", header, 0, b"VPAK", 1, 64, 3)
    struct.pack_into("<5I", header, 16, 0, len(text), len(aux), 64, 128)
    return bytes(header) + text + b"\0" * 48 + aux


class ExportTableTests(unittest.TestCase):
    def test_align8(self):
        self.assertEqual(align8(40 + 25), 72)
        self.assertEqual(align8(40 + 24), 64)

    def test_valid_chain(self):
        result = inspect_export_entries(parse_chunks(fixture()))
        self.assertEqual(result["entries"], 3)
        self.assertEqual(result["consecutive_offset_transitions"], 2)
        self.assertEqual(result["terminal_zero_markers"], 1)
        self.assertEqual(result["distinct_first_word_values"], 1)
        self.assertEqual(result["nonterminal_length_past_data"], 0)

    def test_no_terminal_zero(self):
        entries = [(0x8E112EB7, 24, 40, 1), (0x8E112EB7, 0, 64, 2)]
        with self.assertRaisesRegex(ValueError, "zero marker"):
            inspect_export_entries(parse_chunks(fixture(entries)))

    def test_premature_zero(self):
        entries = [(0x8E112EB7, 24, 40, 0), (0x8E112EB7, 0, 64, 0)]
        with self.assertRaisesRegex(ValueError, "zero marker"):
            inspect_export_entries(parse_chunks(fixture(entries)))

    def test_offset_chain_break(self):
        entries = [(0x8E112EB7, 24, 40, 1), (0x8E112EB7, 0, 72, 0)]
        with self.assertRaisesRegex(ValueError, "offset chain"):
            inspect_export_entries(parse_chunks(fixture(entries)))

    def test_misaligned_offset(self):
        entries = [(0x8E112EB7, 24, 41, 1), (0x8E112EB7, 0, 72, 0)]
        with self.assertRaisesRegex(ValueError, "alignment"):
            inspect_export_entries(parse_chunks(fixture(entries)))

    def test_length_overrun_report_not_fatal(self):
        entries = [(0x8E112EB7, 80, 88, 1), (0x8E112EB7, 0, 168, 0)]
        result = inspect_export_entries(parse_chunks(fixture(entries, data_size=160)))
        self.assertEqual(result["nonterminal_length_past_data"], 1)
        self.assertEqual(result["nonterminal_length_past_data_indices"], [0])


if __name__ == "__main__":
    unittest.main()
