#!/usr/bin/env python3
"""V104 original-free translated IOS_OpenAsync request boundary tests."""
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v103_sc_async_entry_harness import derive as previous
from derive_v104_sc_async_submit_harness import EDITS,derive
from derive_v104_sc_async_submit_generator import derive as generator
from derive_v104_sc_async_submit_runner import derive as runner
from restore_sc_async_submit_v104 import ROOT,SIZE,EDGES,EXPECTED,restore
from extend_private_text import NOP
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
class AsyncSubmitV104(unittest.TestCase):
    def test_fixture(self):
        raw=bytearray(256)
        for k,v in ((0,256),(0x48,ROOT),(0x90,SIZE)):
            struct.pack_into(">I",raw,k,v)
        raw.extend(EXPECTED)
        body=bytearray(NOP*(SIZE//4))
        for pc,dst in EDGES:
            struct.pack_into(">I",body,pc-ROOT,0x48000001|((dst-pc)&0x03fffffc))
        struct.pack_into(">I",body,SIZE-4,BLR)
        got=restore(bytes(raw),bytes(body))
        self.assertEqual(got[:256],raw[:256])
        self.assertEqual(got[256:],bytes(body))
        with self.assertRaises(ValueError):restore(got,bytes(body))
        for pc,dst in EDGES:
            bad=bytearray(body);bad[pc-ROOT:pc-ROOT+4]=NOP
            with self.subTest(pc=pc),self.assertRaises(ValueError):restore(bytes(raw),bytes(bad))
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);actual=derive(base)
        for old,new in EDITS:self.assertEqual(prior.count(old),1,old[:70])
        self.assertEqual(actual,derive(base))
        for marker in ("V104_ASYNC_SAVE","V104_ASYNC_CACHE","V104_ASYNC_SYSCALL","V104_ASYNC_SUBMIT",
                       "V104_TRIAL_PASS","POST_OWNER=0x805195ecu"):
            self.assertEqual(actual.count(marker),1,marker)
        for label in ("post104_save","post104_alloc_head","post104_alloc","post104_disable",
                      "post104_restore","post104_flush","post104_sc","post104_submit","post104_trace"):
            self.assertIn("nwii::runtime::"+label+"=",actual)
        self.assertIn("nwii::runtime::post104_flush=nwii::runtime::post104_sc=nwii::runtime::post104_submit=nwii::runtime::post104_trace=0",actual)
        self.assertIn("nwii::runtime::post104_flush_before=0",actual)
        self.assertIn("V104 IOS_OpenAsync native cache syscall order or line count differs",actual)
        self.assertEqual(actual.count("V104_TRACE seq="),1)
        self.assertIn("ctx.lr==0x8051ab64u&&post103_alloc==1u&&post103_async==0u",actual)
        self.assertIn("ctx.lr==0x8051ad14u&&post103_alloc==1u&&post103_async==0u",actual)
        self.assertIn("ctx.lr==0x8051ab64u&&post104_alloc==1u",actual)
        self.assertIn("ctx.lr==0x8051ad14u&&post104_alloc==1u",actual)
        self.assertEqual(actual.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(actual.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_runner(self):
        g=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V104 authentic IOS_OpenAsync dependency differs",g)
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104",s)
        self.assertLess(s.index("restore_sc_async_entry_v103.py"),s.index("restore_sc_async_submit_v104.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
