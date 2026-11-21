#!/usr/bin/env python3
"""V240 owner-original first reply callback/source ABI regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v240_sc_first_callback_abi_harness import derive, PROBE_ANCHOR, PROBE, SEND, NEXT_EXTRA
from derive_v240_sc_first_callback_abi_runner import derive as runner, ENTRY, PATTERN, PASS
from derive_v239_sc_isfs_caller_return_harness import derive as previous
HERE=Path(__file__).resolve().parent
class V240(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_first_reply_callback_registry_and_second_prologue(self):
        for marker in ("ipc70_ram.read32(v153_phys+32u)",
                       "ipc70_ram.read32(v153_phys+36u)",
                       "v240_obs_cb==0x804f0e04u",
                       "v240_obs_cb==0x804f1e2cu",
                       "ctx.gpr[3]==v240_obs_result",
                       "ctx.gpr[4]==v240_obs_user",
                       "ctx.ctr==v240_obs_cb",
                       "v239_return_pc==0x805192acu",
                       "V240_FIRST_CB"):
            self.assertIn(marker,PROBE)
        for marker in ("V240_CB_CHAIN","++v240_submit_seen",
                       "v240_seen&&v240_first&&v240_ipc_return"):
            self.assertIn(marker,SEND)
        self.assertIn(PROBE_ANCHOR+"\n"+PROBE,self.after)
        self.assertIn(NEXT_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("mismatched source")
    def test_only_reads_registered_callback_and_no_guest_writes(self):
        for marker in ("ipc70_bus.write32(","ipc70_ram.write8(",
                       "ctx.mmu.write32(","scheduler.service_one("):
            self.assertEqual(self.before.count(marker),self.after.count(marker))
        for snippet in (PROBE,SEND):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                        "<<v240_obs_cb","<<v240_obs_user","<<v240_obs_result",
                        "ctx.gpr[3]=","ctx.gpr[4]="):
                self.assertNotIn(bad,snippet)
    def test_16_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("derive_v240_sc_first_callback_abi_harness.py",
                  "V239_SC_ISFS_CALLER verified=1",
                  "V240_SC_FIRST_CALLBACK verified=1"):
            self.assertIn(m,script)
        good="V240_CB_CHAIN seen=1 first=1 reply=1 cb_isfsfunc=1 cb_isfsopen=0 cb_text=1 r3_reply=1 r4_userdata=1 ctr_cb=1 ctr_isfsopen=0 ipc_return=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("first=1","first=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("ipc_return=1","ipc_return=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v240-sc-first-callback-abi.yml").read_text()
        for m in ("run_v240_sc_first_callback_abi.sh",
                  "test_v240_sc_first_callback_abi.py",
                  "V240_SC_FIRST_CALLBACK verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v240_sc_first_callback_abi.sh").read_text())):
                p=Path(tmp)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
