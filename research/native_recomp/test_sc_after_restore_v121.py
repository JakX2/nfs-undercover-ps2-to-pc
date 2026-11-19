#!/usr/bin/env python3
"""V121 original-free dynamic next-call checkpoint regression tests."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from derive_v120_sc_x1_sleep_harness import derive as previous
from derive_v121_sc_after_restore_harness import EDITS,derive
from derive_v121_sc_after_restore_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V121(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        prior=previous(base)
        actual=derive(base)
        expected=prior
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:85])
            expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected)
        self.assertEqual(actual,derive(base))
        for m in ("V121_NEXT_CALL pc=",
                  "post121_next==1u&&nwii::runtime::post120_restore==1u",
                  "post121_next_pc=addr;post121_next_lr=ctx.lr;",
                  "nwii::runtime::post90_target:POST_SYNTH"):
            self.assertIn(m,actual)
        self.assertEqual(actual.count("V121_END_IPC ack="),1)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(marker),prior.count(marker))

    def test_runner(self):
        base=(HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8")
        result=runner(base)
        for m in ("V121_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=121",
                  "V121_NATIVE_EXIT ok=1"):
            self.assertIn(m,result)
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"run.sh"
            f.write_text(result,encoding="utf-8")
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v121-sc-after-restore.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for f in ("run_v121_continuous_sc_after_restore.sh",
                  "diagnose_sc_after_restore_v121.py"):
            self.assertTrue((HERE/f).is_file(),f)
            self.assertIn(f,wf)
        for m in ("'.github/workflows/wii-v121-sc-after-restore.yml'",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x[0-9A-F]{8} stage=121",
                  "V121_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,wf)

if __name__=="__main__":
    unittest.main()
