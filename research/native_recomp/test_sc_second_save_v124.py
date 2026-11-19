#!/usr/bin/env python3
"""V124 original-free second register-save continuation regression."""
from pathlib import Path
import unittest,subprocess,tempfile
from derive_v123_sc_post_leaf_harness import derive as previous
from derive_v124_sc_second_save_harness import derive,EDITS
from derive_v124_sc_second_save_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V124(unittest.TestCase):
    def test_harness(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src);actual=derive(src);expected=old
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:95]);expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected);self.assertEqual(actual,derive(src))
        for m in ("V124_NEXT_CALL pc=",
                  "addr==0x80545150u&&ctx.lr==0x8051de54u",
                  "post124_next==1u&&nwii::runtime::post123_next==1u",
                  "nwii::runtime::post90_target==nwii::runtime::post124_pc&&"):
            self.assertIn(m,actual)
        for m in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(m),old.count(m))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("V124_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "V123_NEXT_CALL pc=80545150 lr=8051de54","stage=124"):
            self.assertIn(m,s)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
    def test_workflow(self):
        s=(HERE.parents[1]/".github/workflows/wii-v124-sc-second-save.yml").read_text()
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)
        for f in ("run_v124_continuous_sc_second_save.sh","diagnose_sc_second_save_v124.py"):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,s)
        for m in ("V123_NEXT_CALL pc=80545150","V124_NEXT_CALL pc=[0-9a-f]{8}",
                  "stage=124","WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,s)
if __name__=="__main__":unittest.main()
