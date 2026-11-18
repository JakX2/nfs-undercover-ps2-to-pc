#!/usr/bin/env python3
"""V91 original-free exact resource fixture and derivation regression."""
import struct
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v90_console_route_harness import derive as previous
from derive_v91_resource_open_harness import EDITS, derive
from derive_v91_resource_open_generator import derive as generator
from derive_v91_resource_open_runner import derive as runner
from restore_resource_init_v91 import ROOT,SPANS,EDGES,BOUNDARIES,restore
from extend_private_text import NOP,STUB,unpack
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
def synthetic():
    raw=bytearray(256)
    for i,(base,size) in enumerate(((0x804f0100,0x28),(0x80518fc8,0x6d10),(0x80522540,0x22c28))):
        data=bytearray(NOP*(size//4))
        if base<=ROOT<base+size:data[ROOT-base:ROOT-base+8]=STUB
        for k,v in zip((0,0x48,0x90),(len(raw),base,len(data))):
            struct.pack_into(">I",raw,k+i*4,v)
        raw.extend(data)
    bodies={pc:bytearray(NOP*(size//4)) for pc,size in SPANS}
    for pc,dest in EDGES:
        base=next(b for b,n in SPANS if b<=pc<b+n)
        struct.pack_into(">I",bodies[base],pc-base,0x48000001|((dest-pc)&0x03fffffc))
    for pc,size in SPANS:struct.pack_into(">I",bodies[pc],size-4,BLR)
    return bytes(raw),{pc:bytes(body) for pc,body in bodies.items()}
class ResourceTest(unittest.TestCase):
    def test_fixture(self):
        raw,bodies=synthetic()
        got=restore(raw,bodies)
        self.assertEqual(got[0xd8:256],raw[0xd8:256])
        spans=unpack(got)
        for pc,body in bodies.items():
            _,_,base,code=next(s for s in spans if s[2]<=pc and pc+len(body)<=s[2]+len(s[3]))
            self.assertEqual(code[pc-base:pc-base+len(body)],body)
        for pc in BOUNDARIES:
            _,_,base,code=next(s for s in spans if s[2]<=pc and pc+8<=s[2]+len(s[3]))
            self.assertEqual(code[pc-base:pc-base+8],STUB)
        with self.assertRaises(ValueError):restore(got,bodies)
        for pc,dest in EDGES:
            bad=dict(bodies);base=next(b for b,n in SPANS if b<=pc<b+n)
            body=bytearray(bad[base]);body[pc-base:pc-base+4]=NOP;bad[base]=bytes(body)
            with self.subTest(pc=pc),self.assertRaises(ValueError):restore(raw,bad)
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V91_RESOURCE_OPEN","V91_RESOURCE_BUFFER","V91_TRIAL_PASS","POST_OWNER=0x80519944u","V90_CONSOLE_ROUTE"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_and_runner(self):
        s=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V91 original resource initializer edge differs",s)
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x80519944 stage=91",script)
        self.assertLess(script.index("restore_post_stm_v89.py"),script.index("restore_resource_init_v91.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(script)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
