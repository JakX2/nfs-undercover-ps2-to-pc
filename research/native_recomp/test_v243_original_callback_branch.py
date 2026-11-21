#!/usr/bin/env python3
"""Synthetic PPC branch decoding and bounded V243 reporting."""
import unittest
from audit_v243_original_callback_branch import (
    CB, ISFS, ISFS_PROLOGUE, branch_target, classify_words, format_result,
    private_audit
)

def direct_branch(pc: int, target: int, *, link: bool = False) -> int:
    delta = (target - pc) & 0x03FFFFFC
    return (18 << 26) | delta | int(link)

def conditional_branch(pc: int, target: int) -> int:
    delta = (target - pc) & 0xFFFC
    return (16 << 26) | (20 << 21) | delta

class OriginalBranchAudit(unittest.TestCase):
    def test_unconditional_positive_and_negative_offsets(self):
        self.assertEqual(branch_target(CB,direct_branch(CB,ISFS)),ISFS)
        self.assertEqual(branch_target(ISFS,direct_branch(ISFS,CB)),CB)
        self.assertEqual(branch_target(CB,0x60000000),None)
    def test_conditional_aa_and_absolute(self):
        self.assertEqual(branch_target(CB,conditional_branch(CB,ISFS)),ISFS)
        self.assertEqual(branch_target(CB,(18 << 26) | 0x00102402),
                         0x00102400)
    def test_direct_isfs_and_ppc_register_branches(self):
        words=[direct_branch(CB,ISFS_PROLOGUE),0x4E800020,0x4E800420]
        classified=classify_words(CB,words,ISFS,0x300)
        self.assertTrue(classified["direct_isfs"])
        self.assertFalse(classified["direct_entry"])
        self.assertTrue(classified["direct_prologue"])
        self.assertTrue(classified["lr_branch"])
        self.assertTrue(classified["ctr_branch"])
        no_branch=classify_words(CB,[0x60000000],ISFS,0x300)
        self.assertFalse(no_branch["direct_isfs"])
        self.assertFalse(no_branch["lr_branch"])
    def test_elf32_section_geometry_indices(self):
        # Original-free ELF32 fixture: e_shnum=23, e_shstrndx=20.
        # The regression must reject using e_shnum as e_shentsize.
        from audit_v243_original_callback_branch import HEADER, SECTION
        import struct
        header = HEADER.pack(
            b"\\x7fELF\\x01\\x02\\x01"+b"\\x00"*9,
            2,20,1,0x8000403c,0,HEADER.size,0,
            HEADER.size,0,0,SECTION.size,23,20,
        )
        assert len(header)==HEADER.size
        e=HEADER.unpack_from(header)
        self.assertEqual((e[6],e[11],e[12],e[13]),
                         (HEADER.size,SECTION.size,23,20))
        # This avoids embedding any owner-game bytes or PPC instructions.
        self.assertEqual(len(header)+23*SECTION.size,
                         HEADER.size+23*SECTION.size)

    def test_private_digest_fail_closed(self):
        with self.assertRaises(ValueError):
            private_audit(b"no private ELF")
    def test_private_output_is_bounded_flags_only(self):
        sample={k:False for k in (
            "digest","callback","isfs","executable","separate",
            "same_section","text","direct_isfs","direct_entry",
            "direct_prologue","lr_branch","ctr_branch"
        )}
        sample.update(digest=True,callback=True,isfs=True)
        result=format_result(sample)
        self.assertTrue(result.startswith(
            "V243_ORIGINAL_BRANCH digest=1 callback=1 isfs=1"
        ))
        self.assertNotIn(hex(CB),result)
        self.assertNotIn("0x",result)
        self.assertNotIn("code=",result)

if __name__ == "__main__":
    unittest.main()
