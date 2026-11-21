#!/usr/bin/env python3
"""Source-only V235 ISFS_OpenAsync native nonvolatile mode ABI tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v234_sc_isfs_origin_harness import derive as previous, NEXT_EXTRA as PREVIOUS_EXTRA
from derive_v235_sc_isfs_helper_abi_harness import derive, TRACE, SEND, NEXT_EXTRA
from derive_v235_sc_isfs_helper_abi_runner import derive as runner, STAGE, PATTERN
HERE=Path(__file__).resolve().parent
class V235(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(src);cls.after=derive(src)
    def test_exact_original_callsite_boundaries(self):
        for x in ("addr==0x80519094u&&ctx.lr==0x804f1e60u",
                  "addr==0x8051ad38u&&ctx.lr==0x804f1e84u",
                  "addr==0x80004338u&&ctx.lr==0x804f1eb4u",
                  "addr==0x8051982cu&&ctx.lr==0x804f1eccu",
                  "ctx.gpr[27]==v234_isfs_mode","ctx.gpr[4]==ctx.gpr[27]",
                  "ctx.gpr[3]==ctx.gpr[30]","V235_HELPER"):
            self.assertIn(x,TRACE)
        for x in ("V235_SUMMARY","v235_stage_mask","v235_source_mask",
                  "++v235_summary_seen"):
            self.assertIn(x,SEND)
        self.assertIn(NEXT_EXTRA,self.after)
        self.assertIn(PREVIOUS_EXTRA,self.after)
        with self.assertRaises(ValueError):derive("unmatched fixture")
    def test_no_guest_or_ios_writes_and_no_private_values(self):
        for m in ("scheduler.service_one(","ipc70_bus.write32(",
                  "ctx.mmu.write32(","ipc70_ram.write8("):
            self.assertEqual(self.before.count(m),self.after.count(m))
        for fragment in (TRACE,SEND):
            for bad in ("ctx.mmu.write","ipc70_ram.write","ipc70_bus.write",
                        "<<ctx.gpr","<<v234_isfs_mode"):
                self.assertNotIn(bad,fragment)
            self.assertNotRegex(fragment,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_owner_runner_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for key in ("derive_v235_sc_isfs_helper_abi_harness.py",
                    "V234_SC_ISFS_ORIGIN verified=1",
                    "V235_SC_ISFS_HELPER_ABI verified=1"):
            self.assertIn(key,script)
        self.assertIsNotNone(re.fullmatch(STAGE,
            "V235_HELPER stage=3 r27valid=1 r27source=1 mode_arg=0 arg_eq_r27=0 buf_eq_r30=1"))
        self.assertIsNotNone(re.fullmatch(PATTERN,
            "V235_SUMMARY stage=15 valid=7 source=7 ios_modevalid=0 ios_eq_r27=1 ios_bufsame=1 isfs=1 ios=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v235-sc-isfs-helper-abi.yml").read_text()
        for key in ("run_v235_sc_isfs_helper_abi.sh","test_v235_sc_isfs_helper_abi.py",
                    "V235_SC_ISFS_HELPER_ABI verified=1"):
            self.assertIn(key,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for name,data in (("runner",script),
                              ("wrapper",(HERE/"run_v235_sc_isfs_helper_abi.sh").read_text())):
                path=Path(tmp)/name;path.write_text(data,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)
if __name__=="__main__":unittest.main()
