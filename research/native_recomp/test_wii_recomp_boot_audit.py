"""Synthetic-only tests for Wii static boot graph, no original game data."""
import unittest
from wii_recomp_preflight import parse_elf, parse_dol, PreflightError
from wii_recomp_boot_audit import decode_branch, audit, sign_extend
from test_wii_recomp_preflight import make_pair


def branch(pc, disp, link=1, absolute=0):
    return decode_branch(pc, (18 << 26) | (disp & 0x3FFFFFC) | (absolute << 1) | link)


class BranchTests(unittest.TestCase):
    def test_sign_extend(self):
        self.assertEqual(sign_extend(0x3FFFFFC, 26), -4)
        self.assertEqual(sign_extend(0x20, 26), 32)

    def test_relative_bl(self):
        self.assertEqual(branch(0x80004000, 0x18).target, 0x80004018)
        self.assertTrue(branch(0x80004000, -4).link)
        self.assertEqual(branch(0x80004000, -4).target, 0x80003FFC)

    def test_absolute_branch(self):
        self.assertEqual(branch(0x80004000, 0x100, absolute=1).target, 0x100)

    def test_conditional_and_indirect(self):
        pc = 0x80004010
        bc = (16 << 26) | 0xFFFC | 1
        self.assertEqual(decode_branch(pc, bc).target, pc - 4)
        self.assertEqual(decode_branch(pc, 0x4E800020).kind, 'bclr')
        self.assertEqual(decode_branch(pc, 0x4E800420).kind, 'bcctr')
        self.assertIsNone(decode_branch(pc, 0x60000000))

    def test_synthetic_function_census(self):
        elf_bytes, dol_bytes = make_pair()
        elf, dol = parse_elf(elf_bytes), parse_dol(dol_bytes)
        out, private = audit(elf, dol)
        self.assertEqual(out['function_count'], 2)
        self.assertEqual(out['function_instruction_words'], 6)
        self.assertEqual(out['paired_single_primary_opcode_4_words'], 0)
        self.assertEqual(out['reachable_by_call_depth']['0'], 1)
        self.assertEqual(private['entry_direct_calls_in_file_order'], [])

    def test_bad_depth(self):
        elf_bytes, dol_bytes = make_pair()
        with self.assertRaises(PreflightError):
            audit(parse_elf(elf_bytes), parse_dol(dol_bytes), depth=9)


if __name__ == '__main__':
    unittest.main()
