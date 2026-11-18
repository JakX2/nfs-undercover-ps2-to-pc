#!/usr/bin/env python3
"""V99 original-free exact overlay and fixture tests."""
import struct
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v98_nand_registration_harness import derive as previous
from derive_v99_post_nand_harness import EDITS, derive
from derive_v99_post_nand_generator import derive as generator
from derive_v99_post_nand_runner import derive as runner
from restore_post_nand_v99 import ROOT,SIZE,NEXT,EDGES,EXPECTED,restore
from extend_private_text import NOP,STUB
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
class PostNandTest(unittest.TestCase):
    def test_fixture(self):
        raw=bytearray(256)
        for i,(addr,body) in enumerate(((ROOT,EXPECTED),(NEXT,NOP*2))):
            for k,v in ((0,len(raw)),(0x48,addr),(0x90,len(body))):
                struct.pack_into(">I",raw,k+4*i,v)
            raw.extend(body)
        body=bytearray(NOP*(SIZE//4))
        for pc,dst in EDGES:struct.pack_into(">I",body,pc-ROOT,0x48000001|((dst-pc)&0x03fffffc))
        struct.pack_into(">I",body,SIZE-4,BLR)
        got=restore(bytes(raw),bytes(body))
        self.assertEqual(got[:256],raw[:256])
        self.assertEqual(got[256:],bytes(body)+STUB)
        with self.assertRaises(ValueError):restore(got,bytes(body))
        for pc,dst in EDGES:
            bad=bytearray(body);bad[pc-ROOT:pc-ROOT+4]=NOP
            with self.subTest(pc=pc),self.assertRaises(ValueError):restore(bytes(raw),bytes(bad))
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V99_SIBLING_MEMORY","V99_TRIAL_PASS","POST_OWNER=0x8051dff4u"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_runner(self):
        g=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V99 original sibling direct edge differs",g)
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051DFF4 stage=99",s)
        self.assertLess(s.index("restore_es_close_v97.py"),s.index("restore_post_nand_v99.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
