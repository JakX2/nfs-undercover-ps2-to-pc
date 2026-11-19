#!/usr/bin/env python3
"""V125 owner-free original SC continuation regression."""
from pathlib import Path
import unittest,subprocess,tempfile
from derive_v124_sc_second_save_harness import derive as previous
from derive_v125_sc_helper_harness import derive,EDITS
from derive_v125_sc_helper_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V125(unittest.TestCase):
    def test_harness(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src);actual=derive(src);expected=old
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:95]);expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected);self.assertEqual(actual,derive(src))
        for m in ("V125_NEXT_CALL pc=","addr==0x8051e5bcu&&ctx.lr==0x8051e054u",
                  "post125_next==1u&&nwii::runtime::post124_next==1u",
                  "nwii::runtime::post90_target==nwii::runtime::post125_pc&&"):
            self.assertIn(m,actual)
        for m in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(m),old.count(m))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "V124_NEXT_CALL pc=8051e5bc lr=8051e054","stage=125"):
            self.assertIn(m,s)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
    def test_workflow(self):
        s=(HERE.parents[1]/".github/workflows/wii-v125-sc-helper.yml").read_text()
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)
        for f in ("run_v125_continuous_sc_helper.sh","diagnose_sc_helper_v125.py"):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,s)
        for m in ("V124_NEXT_CALL pc=8051e5bc","V125_NEXT_CALL pc=[0-9a-f]{8}",
                  "stage=125","WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,s)
if __name__=="__main__":unittest.main()
