#!/usr/bin/env python3
"""V273 original-free synthetic PowerPC store provenance regression."""
import unittest
from pathlib import Path
from audit_v273_sc_provenance import resolve,classify_function,audit

START=0x8052f830
def li(r,v):return (14<<26)|(r<<21)|(v&0xffff)
def addi(dst,src,v):return (14<<26)|(dst<<21)|(src<<16)|(v&0xffff)
def mr(dst,src):return (31<<26)|(src<<21)|(dst<<16)|(src<<11)|(444<<1)
def ori(dst,src,imm):return (24<<26)|(src<<21)|(dst<<16)|(imm&0xffff)
def lbz(dst,base,off):return (34<<26)|(dst<<21)|(base<<16)|(off&0xffff)
def stb(src,base,off):return (38<<26)|(src<<21)|(base<<16)|(off&0xffff)

class Tests(unittest.TestCase):
    def test_copy_add_and_immediate_bitwise(self):
        seq=[li(6,1),mr(5,6),addi(5,5,2),stb(5,13,-3176)]
        self.assertEqual(resolve(seq,3,5),("const",3))
        self.assertEqual(classify_function(START,seq)["c3"],1)
        seq=[li(4,1),ori(5,4,2),stb(5,13,-3176)]
        self.assertEqual(resolve(seq,2,5),("const",3))
        for n in (0,1,2,3,255):
            seq=[li(3,n),stb(3,13,-3176)]
            self.assertEqual(resolve(seq,1,3),("const",n))

    def test_status_load_noop_and_unknown(self):
        seq=[lbz(4,13,-3176),ori(0,0,0),stb(4,13,-3176)]
        self.assertEqual(resolve(seq,2,4),("status",-1))
        seq=[lbz(4,13,-3000),stb(4,13,-3176)]
        self.assertEqual(resolve(seq,1,4),("load",-1))

    def test_control_flow_and_unsupported_writes_fail_closed(self):
        cases=(
            [li(4,3),0x48000005,stb(4,13,-3176)],
            [li(4,3),0x41820008,stb(4,13,-3176)],
            [li(4,3),0x7c000000,stb(4,13,-3176)],
        )
        for seq in cases:
            with self.subTest(seq=seq[1]):
                self.assertEqual(resolve(seq,2,4),("unknown",-1))
        with self.assertRaisesRegex(ValueError,"geometry"):
            resolve([stb(3,13,-3176)],1,33)

    def test_sha_gate_and_private_runner(self):
        with self.assertRaisesRegex(ValueError,"digest"):
            audit(b"not the original Wii executable")
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v273-sc-provenance.yml").read_text(encoding="utf-8")
        self.assertIn("V273_PROVENANCE_AUDIT verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
