#!/usr/bin/env python3
"""Original-free positive/negative tests for bounded PPC next-stage scanner."""
import struct
import unittest

from probe_next_osinit_v33 import START,branch_target,classify


def bl(site:int,target:int)->int:
    diff=target-site
    if diff%4 or diff<-(1<<25) or diff>=(1<<25):
        raise ValueError("test PPC BL out of bounds")
    return 0x48000001|(diff&0x03FFFFFC)


class ProbeTests(unittest.TestCase):
    def test_forward_backward_calls(self):
        site=START+4
        code=struct.pack(">3I",bl(START,START+0x20),bl(site,START-0x20),0x4E800020)
        counts,calls=classify(code)
        self.assertEqual(counts["direct_calls"],2)
        self.assertEqual(calls,[(START,START+0x20),(site,START-0x20)])

    def test_absolute_branch(self):
        self.assertEqual(branch_target(0x48001003,START),0x1000)

    def test_malformed_ppc_branch_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"not a direct"):
            branch_target(0x7C0004AC,START)

    def test_opcode_classes_without_guest_code(self):
        # Entire test is independent hand-assembled synthetic stimulus.
        ops=[0x41820008,0x48000008,0x8061000C,0x90010010,
             0x44000002,0x7C6002A6,0x60000000]
        counts,calls=classify(struct.pack(">"+("I"*len(ops)),*ops))
        self.assertFalse(calls)
        for name in ("conditional_branches","direct_branches","loads",
                     "stores_or_fp_memory","syscalls","extended_integer_or_spr","other"):
            self.assertEqual(counts[name],1)

    def test_bad_span_rejected(self):
        for code in (b"",b"\0",b"\0"*5,b"\0"*4100):
            with self.subTest(size=len(code)),self.assertRaises(ValueError):
                classify(code)


if __name__=="__main__":
    unittest.main()
