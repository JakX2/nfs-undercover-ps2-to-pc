#!/usr/bin/env python3
"""V100 original-free SC status overlay and private-body restoration invariants."""
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v99_post_nand_harness import derive as previous
from derive_v100_sc_status_harness import EDITS,derive
from derive_v100_sc_status_generator import derive as generator
from derive_v100_sc_status_runner import derive as runner
from restore_sc_status_v100 import SPANS,EDGES,NEXT,restore
from extend_private_text import NOP,STUB
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
class ScStatusV100(unittest.TestCase):
    def test_fixture(self):
        raw=bytearray(256);bodies={}
        for i,(addr,size) in enumerate(SPANS):
            before=STUB+NOP*(size//4-2) if i==0 else NOP*(size//4)
            for k,v in ((0,len(raw)),(0x48,addr),(0x90,size)):
                struct.pack_into(">I",raw,k+4*i,v)
            raw.extend(before);bodies[addr]=bytearray(NOP*(size//4))
            struct.pack_into(">I",bodies[addr],size-4,BLR)
        for pc,dst in EDGES:
            struct.pack_into(">I",bodies[SPANS[0][0]],pc-SPANS[0][0],0x48000001|((dst-pc)&0x03fffffc))
        addr=NEXT
        for k,v in ((0,len(raw)),(0x48,addr),(0x90,8)):
            struct.pack_into(">I",raw,k+4*len(SPANS),v)
        raw.extend(NOP*2)
        bodies={a:bytes(v) for a,v in bodies.items()}
        out=restore(bytes(raw),bodies)
        self.assertEqual(out[:256],raw[:256])
        self.assertEqual(out[256:],b"".join(bodies[a] for a,n in SPANS)+STUB)
        with self.assertRaises(ValueError):restore(out,bodies)
        for pc,dst in EDGES:
            bad=dict(bodies);x=bytearray(bad[SPANS[0][0]])
            x[pc-SPANS[0][0]:pc-SPANS[0][0]+4]=NOP
            bad[SPANS[0][0]]=bytes(x)
            with self.subTest(pc=pc),self.assertRaises(ValueError):restore(bytes(raw),bad)
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);actual=derive(base)
        for old,new in EDITS:self.assertEqual(prior.count(old),1,old[:70])
        self.assertEqual(actual,derive(base))
        for marker in ("V100_SC_ENTRY","V100_SC_STATUS","V100_SC_ROUTE",
                       "V100_TRIAL_PASS","POST_OWNER=0x8051dd50u"):
            self.assertEqual(actual.count(marker),1,marker)
        self.assertEqual(actual.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(actual.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_runner(self):
        g=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V100 original SC status edge differs",g)
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051DD50 stage=100",s)
        self.assertLess(s.index("restore_post_nand_v99.py"),s.index("restore_sc_status_v100.py"))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
