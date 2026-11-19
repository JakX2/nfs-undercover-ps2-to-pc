#!/usr/bin/env python3
"""V123 original-free second helper continuation regression."""
from pathlib import Path
import unittest,subprocess,tempfile
from derive_v122_sc_post_save_harness import derive as previous
from derive_v123_sc_post_leaf_harness import EDITS,derive
from derive_v123_sc_post_leaf_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V123(unittest.TestCase):
    def test_harness(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(source);actual=derive(source);expected=prior
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:95])
            expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected)
        self.assertEqual(actual,derive(source))
        for marker in ("V123_NEXT_CALL pc=","addr==0x8054514cu&&ctx.lr==0x804f1ed4u",
                       "post123_next==1u&&nwii::runtime::post122_next==1u",
                       "nwii::runtime::post90_target==nwii::runtime::post123_pc&&"):
            self.assertIn(marker,actual)
        for m in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(m),prior.count(m))
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("V123_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "V122_NEXT_CALL pc=8054514c lr=804f1ed4","stage=123"):
            self.assertIn(m,s)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
    def test_workflow(self):
        s=(HERE.parents[1]/".github/workflows/wii-v123-sc-post-leaf.yml").read_text()
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)
        for f in ("run_v123_continuous_sc_post_leaf.sh","diagnose_sc_post_leaf_v123.py"):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,s)
        for m in ("V122_NEXT_CALL pc=8054514c","V123_NEXT_CALL pc=[0-9a-f]{8}",
                  "stage=123","WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,s)
if __name__=="__main__":unittest.main()
