#!/usr/bin/env python3
"""V94 original-free exact overlay and owner-only fixture geometry tests."""
import struct
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v93_isfs_return_harness import derive as previous
from derive_v94_es_open_harness import EDITS, derive
from derive_v94_es_open_generator import derive as generator
from derive_v94_es_open_runner import derive as runner
from restore_title_query_v94 import ROOT,SIZE,CALL,DEST,EXPECTED,restore
from extend_private_text import NOP,STUB
from make_osinit_execparams_v28 import BLR
HERE=Path(__file__).resolve().parent
class EsOpenTest(unittest.TestCase):
    def test_fixture(self):
        raw=bytearray(256)
        for i,(addr,data) in enumerate(((ROOT,EXPECTED),(DEST,NOP*2))):
            for k,v in ((0,len(raw)),(0x48,addr),(0x90,len(data))):
                struct.pack_into(">I",raw,k+4*i,v)
            raw.extend(data)
        body=bytearray(NOP*(SIZE//4))
        struct.pack_into(">I",body,CALL-ROOT,0x48000001|((DEST-CALL)&0x03fffffc))
        struct.pack_into(">I",body,SIZE-4,BLR)
        got=restore(bytes(raw),bytes(body))
        self.assertEqual(got[:256],raw[:256])
        self.assertEqual(got[256:],body+STUB)
        with self.assertRaises(ValueError):restore(got,bytes(body))
        body[CALL-ROOT:CALL-ROOT+4]=NOP
        with self.assertRaises(ValueError):restore(bytes(raw),bytes(body))
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V94_ES_ACK","V94_ES_RETURN","V94_TITLE_REQUEST","V94_TRIAL_PASS","POST_OWNER=0x8051a62cu"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
        self.assertEqual(s.count("ipc70_ram.read32(submit72_phys+4u)==(post94_active?3u:post92_active?2u:open84_active?1u:0u)&&"),4)
    def test_generator_runner(self):
        g=generator((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V94 original title query call edge differs",g)
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051A62C stage=94",s)
        self.assertLess(s.index("restore_next_resource_v93.py"),s.index("restore_title_query_v94.py"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
