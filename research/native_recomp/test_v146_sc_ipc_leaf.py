#!/usr/bin/env python3
"""Original-free V146 native SC IPC handler leaf and runner safety tests."""
import re,subprocess,tempfile,unittest
from pathlib import Path
from derive_v145_sc_ipc_handler_harness import derive as previous
from derive_v146_sc_ipc_leaf_harness import derive,STATE,RESET,STOP,TRIAL,NEXT,NEXT_TRIAL
from derive_v146_sc_ipc_leaf_runner import derive as runner

HERE=Path(__file__).resolve().parent

class V146(unittest.TestCase):
    def test_preserves_original_guest_code_and_sc_ios_pending(self):
        old=previous((HERE/"test_start_to_ipc_ack_v77.cpp").read_text())
        for anchor in (STATE,RESET,STOP,TRIAL):
            self.assertEqual(old.count(anchor),1,anchor[:80])
        now=derive((HERE/"test_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn(NEXT,now)
        self.assertIn(NEXT_TRIAL,now)
        self.assertIn("ctx.inst_count>v146_enter_inst",now)
        self.assertIn("ctx.lr>=0x80519318u&&ctx.lr<0x805194c4u",now)
        self.assertEqual(now.count("V146_SC_IPC_LEAF call="),1)
        for term in ("ctx.mmu.write8(", "ctx.mmu.write32(", "ipc70_ram.write8("):
            self.assertEqual(now.count(term),old.count(term))
        for pat in (r"ctx\.gpr\[3\]\s*=(?!=)",r"ctx\.cr\[0\]\.eq\s*=(?!=)"):
            self.assertEqual(len(re.findall(pat,now)),len(re.findall(pat,old)))

    def test_runner_requires_all_sixteen_owners(self):
        src=(HERE/"run_v79_continuous_reply_entry.sh").read_text()
        script=runner(src)
        for term in ("derive_v146_sc_ipc_leaf_harness.py",
                     "V144_SC_DISABLE verified=1","V145_SC_IPC verified=1",
                     "V146_SC_IPC_LEAF verified=1",
                     "BOOT_PROGRESS entry=0x8000403C"):
            self.assertIn(term,script)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"run.sh";path.write_text(script)
            subprocess.run(["bash","-n",str(path)],check=True)

    def test_missing_anchors_fail_closed(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")

    def test_private_workflow_preserves_owner_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v146-sc-ipc-leaf.yml").read_text()
        self.assertIn("run_v146_sc_ipc_leaf.sh",wf)
        self.assertIn("V146_SC_IPC_LEAF verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
