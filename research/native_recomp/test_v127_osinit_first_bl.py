#!/usr/bin/env python3
"""V127 original-free owner-preserving OSInit first BL checkpoint regression."""
from pathlib import Path
import unittest,tempfile,subprocess
from derive_v125_sc_helper_harness import derive as previous
from derive_v127_osinit_first_bl_harness import derive,EDITS
from derive_v127_osinit_first_bl_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V127(unittest.TestCase):
    def test_harness(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        previous_source=previous(source)
        expected=previous_source
        for old,new in EDITS:
            self.assertEqual(expected.count(old),1,old[:95])
            expected=expected.replace(old,new,1)
        expected=expected.replace("post126_","post127_").replace("V126","V127")
        expected=expected.replace(
           "V127 recovered continuous original __start->SC IOS post-helper GPR-save and next call",
           "V127 recovered original OSInit first authenticated BL after post-SC GPR save")
        actual=derive(source)
        self.assertEqual(actual,expected)
        self.assertIn("V127_NEXT_CALL pc=",actual)
        self.assertIn("addr==0x80545150u&&ctx.lr==0x8051e05cu",actual)
        self.assertNotIn("V126_OSINIT_RETURN pc=",actual)
        for marker in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(marker),previous_source.count(marker))
    def test_runner(self):
        actual=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for marker in ("make_v125_canonical_fixture.py",
                       "V125_CANONICAL result=verified","restore_v127_osinit_tail.py",
                       "V127_OSINIT_RESTORE ok=1","derive_v127_osinit_first_bl_generator.py",
                       "V127_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                       "V125_NEXT_CALL pc=80545150 lr=8051e05c",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=127",
                       "V127_NATIVE_EXIT ok=1"):
            self.assertIn(marker,actual)
        self.assertIn("V127_NATIVE_COUNTS start=",actual)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"run.sh";path.write_text(actual)
            subprocess.run(["bash","-n",str(path)],check=True)
    def test_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v127-osinit-first-bl.yml").read_text()
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for marker in ("run_v127_continuous_osinit_first_bl.sh",
                       "restore_v127_osinit_tail.py","V127_OSINIT_RESTORE ok=1",
                       "V127_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                       "V125_CANONICAL result=verified",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x[0-9A-F]{8} stage=127",
                       "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(marker,wf)
        self.assertTrue((HERE/"run_v127_continuous_osinit_first_bl.sh").is_file())
if __name__=="__main__":
    unittest.main()
