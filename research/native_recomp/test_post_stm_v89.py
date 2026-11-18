#!/usr/bin/env python3
"""V89 original-free guards for exact next subsystem restoration."""
import struct
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v88_stm_return_harness import derive as previous
from derive_v89_post_stm_harness import EDITS, derive
from derive_v89_post_stm_generator import derive as generator
from derive_v89_post_stm_runner import derive as runner
from restore_post_stm_v89 import OS_CALL, ROOT, SIZE, EDGES, BOUNDARIES, OLD_OS, STUB, EMPTY, restore
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent

def branch(pc,dest):
    return struct.pack(">I",0x48000001|((dest-pc)&0x03fffffc))

def synthetic():
    header=bytearray(256)
    payload=bytearray()
    for i,(pc,body) in enumerate(((OS_CALL,OLD_OS),(ROOT,EMPTY*(SIZE//4)),
                                (BOUNDARIES[0],EMPTY*2),(BOUNDARIES[1],EMPTY*2))):
        for off,val in ((0,256+len(payload)),(0x48,pc),(0x90,len(body))):
            struct.pack_into(">I",header,off+4*i,val)
        payload.extend(body)
    body=bytearray(EMPTY*(SIZE//4))
    for pc,dest in EDGES:
        body[pc-ROOT:pc-ROOT+4]=branch(pc,dest)
    struct.pack_into(">I",body,SIZE-4,BLR)
    return bytes(header+payload),bytes(body)

class PostStmTest(unittest.TestCase):
    def test_fixture(self):
        prior,body=synthetic()
        got=restore(prior,branch(OS_CALL,ROOT),body)
        self.assertEqual(got[:256],prior[:256])
        self.assertEqual(got[256:],branch(OS_CALL,ROOT)+STUB+body+STUB+STUB)
        for pc,_ in EDGES:
            bad=bytearray(body);bad[pc-ROOT:pc-ROOT+4]=EMPTY
            with self.subTest(pc=pc),self.assertRaises(ValueError):
                restore(prior,branch(OS_CALL,ROOT),bytes(bad))
        with self.assertRaises(ValueError):
            restore(prior,EMPTY,body)
        with self.assertRaises(ValueError):
            restore(got,branch(OS_CALL,ROOT),body)
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:
            self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V89_SUBSYSTEM","V89_TRIAL_PASS","POST_OWNER=0x8051fd44u","V88_STM_RETURN"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_and_runner(self):
        s=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V89 original subsystem call edge differs",s)
        self.assertIn("OS_RET_STOP=0x8052096c",s)
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051FD44 stage=89",script)
        self.assertLess(script.index("restore_stm_ioctl_v86.py"),script.index("restore_post_stm_v89.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(script)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
