#!/usr/bin/env python3
"""V101 original-free exact SC loading overlay and fixture tests."""
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v100_sc_status_harness import derive as previous
from derive_v101_sc_loading_harness import EDITS,derive
from derive_v101_sc_loading_generator import derive as generator
from derive_v101_sc_loading_runner import derive as runner
from restore_sc_loading_v101 import ROOT,SIZE,TARGETS,EDGES,EXPECTED,restore
from extend_private_text import NOP,STUB
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
class ScLoadingV101(unittest.TestCase):
    def test_fixture(self):
        raw=bytearray(256)
        for i,(addr,data) in enumerate(((ROOT,EXPECTED),*( (target,NOP*2) for target in TARGETS))):
            for k,value in ((0,len(raw)),(0x48,addr),(0x90,len(data))):
                struct.pack_into(">I",raw,k+4*i,value)
            raw.extend(data)
        body=bytearray(NOP*(SIZE//4))
        for pc,dst in EDGES:
            struct.pack_into(">I",body,pc-ROOT,0x48000001|((dst-pc)&0x03fffffc))
        struct.pack_into(">I",body,SIZE-4,BLR)
        result=restore(bytes(raw),bytes(body))
        self.assertEqual(result[:256],raw[:256])
        self.assertEqual(result[256:],bytes(body)+STUB*len(TARGETS))
        with self.assertRaises(ValueError):restore(result,bytes(body))
        for pc,dst in EDGES:
            altered=bytearray(body);altered[pc-ROOT:pc-ROOT+4]=NOP
            with self.subTest(pc=pc),self.assertRaises(ValueError):restore(bytes(raw),bytes(altered))
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);derived=derive(base)
        for old,new in EDITS:self.assertEqual(prior.count(old),1,old[:70])
        self.assertEqual(derived,derive(base))
        for marker in ("V101_SC_SAVE","V101_SC_CHILD","V101_TRIAL_PASS","POST_OWNER=0x8051e71cu"):
            self.assertEqual(derived.count(marker),1,marker)
        self.assertEqual(derived.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(derived.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_runner(self):
        g=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V101 original SC configuration direct edge differs",g)
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051E71C stage=101",s)
        self.assertLess(s.index("restore_sc_status_v100.py"),s.index("restore_sc_loading_v101.py"))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
