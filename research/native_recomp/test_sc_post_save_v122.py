#!/usr/bin/env python3
"""V122 original-free register-save and next-call validation."""
from pathlib import Path
import tempfile,subprocess,unittest
from derive_v121_sc_after_restore_harness import derive as previous
from derive_v122_sc_post_save_harness import EDITS,derive
from derive_v122_sc_post_save_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V122(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(base);actual=derive(base);expected=old
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:95]);expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected)
        for m in ("V121_NEXT_CALL pc=","V122_NEXT_CALL pc=",
                  "addr==0x80545150u&&ctx.lr==0x80519934u",
                  "post122_next==1u&&nwii::runtime::post121_next==1u",
                  "nwii::runtime::post90_target==nwii::runtime::post122_pc&&"):
            self.assertIn(m,actual)
        for m in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(m),old.count(m))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("V122_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "V121_NEXT_CALL pc=80545150 lr=80519934",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=122"):
            self.assertIn(m,s)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(s);subprocess.run(["bash","-n",str(p)],check=True)
    def test_workflow(self):
        s=(HERE.parents[1]/".github/workflows/wii-v122-sc-post-save.yml").read_text()
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)
        for f in ("run_v122_continuous_sc_post_save.sh","diagnose_sc_post_save_v122.py"):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,s)
        for m in ("V121_NEXT_CALL pc=80545150","V122_NEXT_CALL pc=[0-9a-f]{8}",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x[0-9A-F]{8} stage=122",
                  "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,s)
if __name__=="__main__":unittest.main()
