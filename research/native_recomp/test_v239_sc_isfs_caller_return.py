#!/usr/bin/env python3
"""V239 original-free saved ISFS caller provenance regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v239_sc_isfs_caller_return_harness import derive, TRACE_ANCHOR, PROBE, SEND, NEXT_EXTRA
from derive_v239_sc_isfs_caller_return_runner import derive as runner, ENTRY, PATTERN, PASS
from derive_v238_sc_isfs_prologue_source_harness import derive as previous
HERE=Path(__file__).resolve().parent
class V239(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base);cls.after=derive(base)
    def test_original_second_saved_return_and_abi(self):
        for s in ("if(seq==2u&&v239_caller_seen==0u)",
                  "caller>=0x80400000u&&caller<0x80600000u",
                  "v239_return_pc=v239_obs_text?caller:0u",
                  "v237_first_lr_mapped&&caller==v237_first_lr",
                  "v239_path_valid=validpath","V239_ISFS_RETURN"):
            self.assertIn(s,PROBE)
        for s in ("V239_ISFS_CHAIN","v238_save_count>=2u",
                  "v239_ready&&v239_text&&v239_invalid","++v239_submit_seen"):
            self.assertIn(s,SEND)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertIn(TRACE_ANCHOR+"\n"+PROBE,self.after)
        with self.assertRaises(ValueError):derive("invalid source")
    def test_no_guest_mutation_or_raw_buffers(self):
        for x in ("ipc70_bus.write32(","ipc70_ram.write8(",
                  "ctx.mmu.write32(","scheduler.service_one("):
            self.assertEqual(self.before.count(x),self.after.count(x))
        for code in (PROBE,SEND):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                        "<<caller<<","<<sp<<","<<pathptr<<","<<chars<<"):
                self.assertNotIn(bad,code)
            self.assertNotRegex(code,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
        self.assertIn("v239_obs_text?caller:0u",PROBE)
    def test_owner_16_trials_and_no_private_artifacts(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for s in ("derive_v239_sc_isfs_caller_return_harness.py",
                  "V238_SC_ISFS_PROLOGUE verified=1",
                  "V239_SC_ISFS_CALLER verified=1"):
            self.assertIn(s,script)
        line="V239_ISFS_RETURN text=1 ipc=1 isfs=0 nand_region=0 os=0 same_first=0 modevalid=0 pathvalid=0 ret=805192ac"
        self.assertIsNotNone(re.fullmatch(ENTRY,line))
        good="V239_ISFS_CHAIN ready=1 text=1 same_first=0 invalid=1 ios_invalid=1 same_ios_mode=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("text=1","text=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("same_first=0","same_first=1")))
        wf=(HERE.parents[1]/".github/workflows/wii-v239-sc-isfs-caller-return.yml").read_text()
        for k in ("run_v239_sc_isfs_caller_return.sh",
                  "test_v239_sc_isfs_caller_return.py",
                  "V239_SC_ISFS_CALLER verified=1"):
            self.assertIn(k,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v239_sc_isfs_caller_return.sh").read_text())):
                p=Path(tmp)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
