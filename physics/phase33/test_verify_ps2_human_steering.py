"""Tests for the Phase 33 PS2 binary verifier. No proprietary fixtures."""
import os
import struct
import unittest
from pathlib import Path
from verify_ps2_human_steering import BUILDS, callers, jal_target, load_segments, verify, word_at


def fake_elf():
    data = bytearray(512)
    data[:16] = b"\x7fELF\x01\x01\x01" + bytes(9)
    struct.pack_into("<H", data, 16, 2)
    struct.pack_into("<H", data, 18, 8)
    struct.pack_into("<I", data, 28, 0x34)
    struct.pack_into("<HH", data, 42, 32, 1)
    struct.pack_into("<8I", data, 0x34, 1, 0x100, 0x400000, 0x400000,
                     0x40, 0x40, 5, 0x100)
    struct.pack_into("<I", data, 0x104, 0x0C100040)
    return bytes(data)


class TestPS2Steering(unittest.TestCase):
    def test_synthetic_segment(self):
        b = fake_elf()
        self.assertEqual(load_segments(b), [(0x400000, 0x100, 0x40)])
        self.assertEqual(word_at(b, load_segments(b), 0x400004), 0x0C100040)

    def test_synthetic_jal(self):
        b = fake_elf()
        self.assertEqual(jal_target(0x0C100040, 0x400004), 0x400100)
        self.assertEqual(callers(b, load_segments(b), 0x400100), [0x400004])

    def test_non_jal_rejected(self):
        with self.assertRaises(ValueError):
            jal_target(0x27BDFF70, 0x400004)

    def test_non_mips_rejected(self):
        b = bytearray(fake_elf())
        struct.pack_into("<H", b, 18, 3)
        with self.assertRaisesRegex(ValueError, "MIPS"):
            load_segments(b)

    def test_truncated_elf_rejected(self):
        with self.assertRaisesRegex(ValueError, "Truncated"):
            load_segments(fake_elf()[:0x115])

    def test_unmapped_rejected(self):
        b = fake_elf()
        with self.assertRaises(ValueError):
            word_at(b, load_segments(b), 0x500000)

    def test_exact_hash_guard(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            verify(fake_elf(), "undercover_ps2")
        with self.assertRaises(ValueError):
            verify(fake_elf(), "unknown")

    def test_distinct_original_builds(self):
        a, b = BUILDS["undercover_ps2"], BUILDS["carbon_ps2"]
        self.assertNotEqual(a["sha"], b["sha"])
        self.assertEqual(a["end"]-a["start"], 1216)
        self.assertEqual(b["end"]-b["start"], 688)

    def test_original_uc_if_provided(self):
        if not os.getenv("UC_PS2_ELF"):
            self.skipTest("Set UC_PS2_ELF for original-game verification")
        r = verify(Path(os.environ["UC_PS2_ELF"]).read_bytes(), "undercover_ps2")
        self.assertEqual((r["instruction_checks"], r["call_checks"]), (19, 4))

    def test_original_carbon_if_provided(self):
        if not os.getenv("CARBON_PS2_ELF"):
            self.skipTest("Set CARBON_PS2_ELF for original-game verification")
        r = verify(Path(os.environ["CARBON_PS2_ELF"]).read_bytes(), "carbon_ps2")
        self.assertEqual((r["instruction_checks"], r["call_checks"]), (9, 3))


if __name__ == "__main__":
    unittest.main()
