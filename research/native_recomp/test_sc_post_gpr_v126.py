#!/usr/bin/env python3
"""V126 original-free post-SC native GPR-save checkpoint regression."""
from pathlib import Path
import subprocess,tempfile,unittest
from derive_v125_sc_helper_harness import derive as previous
from derive_v126_sc_post_gpr_harness import derive,EDITS
from derive_v126_sc_post_gpr_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V126(unittest.TestCase):
    def test_harness(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src);actual=derive(src);expected=old
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:90])
            expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected)
        self.assertEqual(actual,derive(src))
        for marker in ("V126_OSINIT_RETURN pc=","addr==0x80545150u&&ctx.lr==0x8051e05cu",
                       "post126_next==1u&&nwii::runtime::post125_next==1u",
                       "nwii::runtime::post90_target==nwii::runtime::post126_pc&&"):
            self.assertIn(marker,actual)
        self.assertIn("ctx.pc==0x8052096cu",actual)
        self.assertIn("ctx.mmu.read32(ctx.pc)==0x44000002u",actual)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(marker),old.count(marker))
    def test_runner(self):
        src=(HERE/"run_v79_continuous_reply_entry.sh").read_text()
        actual=runner(src)
        self.assertIn("V126_OSINIT_RETURN pc=[0-9a-f]{8} lr=[0-9a-f]{8}",actual)
        for marker in ("make_v125_canonical_fixture.py",
                       "V125_CANONICAL result=verified",
                       "V125_NEXT_CALL pc=80545150 lr=8051e05c",
                       "V126_OSINIT_RETURN pc=8052096c lr=8052096c",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x8052096C stage=126",
                       "V126_NATIVE_EXIT ok=1"):
            self.assertIn(marker,actual)
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"run.sh";f.write_text(actual)
            subprocess.run(["bash","-n",str(f)],check=True)
    def test_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v126-sc-post-gpr.yml").read_text()
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for name in ("make_v125_canonical_fixture.py","run_v126_continuous_sc_post_gpr.sh",
                     "diagnose_sc_post_gpr_v126.py",
                     "V125_CANONICAL result=verified",
                     "V125_NEXT_CALL pc=80545150 lr=8051e05c",
                     "V126_OSINIT_RETURN pc=8052096c lr=8052096c",
                     "BOOT_PROGRESS entry=0x8000403C pc=0x8052096C stage=126",
                     "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(name,wf)
        for p in ("run_v126_continuous_sc_post_gpr.sh","diagnose_sc_post_gpr_v126.py"):
            self.assertTrue((HERE/p).is_file())
if __name__=="__main__":unittest.main()
