#!/usr/bin/env python3
"""Original-free geometry, width and fail-closed tests for SC SDA writer audit."""
import struct
import unittest
from audit_sc_status_writer_sites import (
    STATUS_OFFSET, STATUS_BASE, STATUS_LOAD_OP, STATUS_REGISTER,
    StoreSite, code_sections, direct_writer_sites, report, verify_status_load,
)


def opword(op, src, base, disp):
    return (op << 26) | (src << 21) | (base << 16) | (disp & 0xFFFF)


def fake_dol(sections):
    raw = bytearray(256)
    for i, (guest, words) in enumerate(sections):
        assert i < 7
        payload = struct.pack(">" + "I" * len(words), *words)
        off = len(raw)
        struct.pack_into(">I", raw, i * 4, off)
        struct.pack_into(">I", raw, 0x48 + i * 4, guest)
        struct.pack_into(">I", raw, 0x90 + i * 4, len(payload))
        raw.extend(payload)
    return bytes(raw)


class ScWriterAudit(unittest.TestCase):
    def test_original_byte_load_contract(self):
        self.assertEqual(STATUS_REGISTER, 29)
        verify_status_load(opword(STATUS_LOAD_OP, STATUS_REGISTER, STATUS_BASE, STATUS_OFFSET))
        for word in (opword(32, 3, 13, STATUS_OFFSET),
                     opword(34, 4, 13, STATUS_OFFSET),
                     opword(34, 3, 1, STATUS_OFFSET),
                     opword(34, 3, 13, STATUS_OFFSET + 1)):
            with self.assertRaises(ValueError):
                verify_status_load(word)

    def test_width_sensitive_direct_writers(self):
        words = [
            opword(38, 4, 13, STATUS_OFFSET),
            opword(36, 5, 13, STATUS_OFFSET - 3),
            opword(44, 6, 13, STATUS_OFFSET - 1),
            opword(54, 7, 13, STATUS_OFFSET - 7),
            opword(47, 30, 13, STATUS_OFFSET - 7),
            opword(38, 4, 13, STATUS_OFFSET + 1),
            opword(36, 4, 13, STATUS_OFFSET - 4),
            opword(38, 4, 1, STATUS_OFFSET),
            opword(34, 3, 13, STATUS_OFFSET),
        ]
        image = fake_dol([(0x80530000, words)])
        sites = direct_writer_sites(image)
        self.assertEqual(len(sites), 5)
        self.assertEqual([s.kind for s in sites], ["stb", "stw", "sth", "stfd", "stmw"])
        self.assertEqual([s.width for s in sites], [1, 4, 2, 8, 8])
        self.assertEqual(len(report(sites)), 6)
        self.assertIn("direct_candidates=5 shown=5 truncated=0", report(sites)[0])

    def test_multiple_sections_and_output_bound(self):
        sections = []
        for i in range(7):
            sections.append((0x80510000 + i * 0x100,
                             [opword(38, 4, 13, STATUS_OFFSET)] * 4))
        sites = direct_writer_sites(fake_dol(sections))
        self.assertEqual(len(sites), 28)
        self.assertEqual(len(report(sites)), 17)
        self.assertIn("truncated=1", report(sites)[0])
        self.assertEqual(sites[0], StoreSite(0x80510000, "stb", 1, STATUS_OFFSET))

    def test_reject_malformed_sections(self):
        with self.assertRaises(ValueError):
            list(code_sections(bytes(100)))
        with self.assertRaises(ValueError):
            list(code_sections(bytes(256)))
        image = bytearray(fake_dol([(0x80530000, [opword(38, 4, 13, STATUS_OFFSET)])]))
        struct.pack_into(">I", image, 0x90, 0x1000)
        with self.assertRaises(ValueError):
            direct_writer_sites(bytes(image))
        image = bytearray(fake_dol([(0x80530000, [0]), (0x80530000, [0])]))
        with self.assertRaises(ValueError):
            direct_writer_sites(bytes(image))

    def test_owner_guard_has_no_original_dump(self):
        from pathlib import Path
        source = Path(__file__).with_name("audit_sc_status_writer_sites.py").read_text()
        self.assertIn("hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA", source)
        self.assertNotIn("print(raw)", source)
        self.assertNotIn("print(word)", source)
        self.assertIn("SC_SDA_WRITERS result=failed", source)


if __name__ == "__main__":
    unittest.main()
