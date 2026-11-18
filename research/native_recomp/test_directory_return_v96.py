#!/usr/bin/env python3
"""V96 original-free exact overlay and fixture tests."""
import struct
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v95_title_return_harness import derive as previous
from derive_v96_directory_return_harness import EDITS, derive
from derive_v96_directory_return_generator import derive as generator
from derive_v96_directory_return_runner import derive as runner
from restore_directory_v96 import ROOT,SIZE,CALL,DEST,EXPECTED,restore
from extend_private_text import NOP
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
class DirectoryReturnTest(unittest.TestCase):
    def test_fixture(self):
        raw=bytearray(256)
        for k,v in ((0,256),(0x48,ROOT),(0x90,SIZE)):
            struct.pack_into(">I",raw,k,v)
        raw.extend(EXPECTED)
        body=bytearray(NOP*(SIZE//4))
        struct.pack_into(">I",body,CALL-ROOT,0x48000001|((DEST-CALL)&0x03fffffc))
        struct.pack_into(">I",body,SIZE-4,BLR)
        got=restore(bytes(raw),bytes(body))
        self.assertEqual(got[:256],raw[:256])
        self.assertEqual(got[256:],body)
        with self.assertRaises(ValueError):restore(got,bytes(body))
        body[CALL-ROOT:CALL-ROOT+4]=NOP
        with self.assertRaises(ValueError):restore(bytes(raw),bytes(body))
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V96_DIRECTORY_REQUEST","V96_VECTOR_SUBMIT","V96_DIRECTORY_ACK","V96_DIRECTORY_RETURN","V96_TRIAL_PASS","POST_OWNER=0x8054b4b4u"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
    def test_generator_runner(self):
        g=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V96 directory query edge differs",g)
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8054B4B4 stage=96",s)
        self.assertLess(s.index("restore_ioctlv_v95.py"),s.index("restore_directory_v96.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
