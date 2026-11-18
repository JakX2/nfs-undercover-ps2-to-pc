#!/usr/bin/env python3
"""V95 original-free exact overlay and fixture checks."""
import struct
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v94_es_open_harness import derive as previous
from derive_v95_title_return_harness import EDITS, derive
from derive_v95_title_return_generator import derive as generator
from derive_v95_title_return_runner import derive as runner
from restore_ioctlv_v95 import SPANS,EDGES,restore
from extend_private_text import NOP,STUB
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
class TitleReturnTest(unittest.TestCase):
    def test_fixture(self):
        raw=bytearray(256);bodies={}
        for i,(addr,size) in enumerate(SPANS):
            data=STUB+NOP*(size//4-2) if i==0 else NOP*(size//4)
            for k,v in ((0,len(raw)),(0x48,addr),(0x90,size)):
                struct.pack_into(">I",raw,k+4*i,v)
            raw.extend(data)
            bodies[addr]=bytearray(NOP*(size//4))
            struct.pack_into(">I",bodies[addr],size-4,BLR)
        for pc,dst in EDGES:
            base=next(a for a,n in SPANS if a<=pc<a+n)
            struct.pack_into(">I",bodies[base],pc-base,0x48000001|((dst-pc)&0x03fffffc))
        bodies={a:bytes(v) for a,v in bodies.items()}
        got=restore(bytes(raw),bodies)
        self.assertEqual(got[:256],raw[:256])
        self.assertEqual(got[256:],b"".join(bodies[a] for a,n in SPANS))
        with self.assertRaises(ValueError):restore(got,bodies)
        for pc,dst in EDGES:
            base=next(a for a,n in SPANS if a<=pc<a+n)
            bad=dict(bodies);data=bytearray(bad[base]);data[pc-base:pc-base+4]=NOP;bad[base]=bytes(data)
            with self.subTest(pc=pc),self.assertRaises(ValueError):restore(bytes(raw),bad)
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V95_VECTOR_SUBMIT","V95_TITLE_ACK","V95_TITLE_RETURN","V95_TRIAL_PASS","POST_OWNER=0x804f0ad8u"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_runner(self):
        g=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V95 original vector body geometry differs",g)
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x804F0AD8 stage=95",s)
        self.assertLess(s.index("restore_title_query_v94.py"),s.index("restore_ioctlv_v95.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
