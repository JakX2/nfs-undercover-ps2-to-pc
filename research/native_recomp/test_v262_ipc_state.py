#!/usr/bin/env python3
"""Synthetic and source-only V262 Wii IPC state sampling regression."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from analyze_v262_ipc_state import parse, summary, count_edges
from derive_v244_sc_callback_link_harness import derive as base
from derive_v261_guest_call_census_harness import derive as previous
from derive_v262_ipc_state_harness import derive, STATE_OBSERVER
from derive_v262_ipc_state_runner import derive as runner

HERE=Path(__file__).resolve().parent

def fixture():
    lines=[]
    for _ in range(16):
        for n in range(1,65):
            ee=int(n%2==0)
            lines.append(
                f"V262_STATE n={n} mapped=1 ee={ee} irq=0 "
                "native_request=0 queued=0 sc=1 reply=1")
    return "\n".join(lines)

class V262(unittest.TestCase):
    def test_synthetic_hardware_state_edges_and_rejects(self):
        s=fixture()
        blocks=parse(s)
        self.assertEqual(len(blocks),16)
        self.assertEqual(count_edges(blocks[0],"ee"),63)
        self.assertIn("stable=1 distinct=1 ee_edges=63 irq_edges=0 "
                      "request_edges=0 queue_edges=0 sc_edges=0",summary(blocks))
        self.assertIn("request_ever=0 queue_max=0 reply_all=1 sc_first=1 sc_last=1",
                      summary(blocks))
        cases=(
            (s.replace("V262_STATE n=3 ","V262_STATE n=5 ",1),
             "out_of_order_state"),
            (s.replace("mapped=1","mapped=0",1),"unmapped_sc_state"),
            (s.replace("V262_STATE n=64 mapped=1 ee=1 irq=0 "
                       "native_request=0 queued=0 sc=1",
                       "V262_STATE n=64 mapped=1 ee=1 irq=0 "
                       "native_request=0 queued=0 sc=0",1),
             "frontier_sc_changed"),
            ("\n".join(s.splitlines()[:-1]),"incomplete_state_window"),
        )
        for invalid,reason in cases:
            with self.subTest(reason=reason),self.assertRaisesRegex(ValueError,reason):
                parse(invalid)

    def test_no_guest_cpu_mmio_or_memory_mutations(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        before=previous(base(source))
        after=derive(base(source))
        self.assertIn(STATE_OBSERVER,after)
        self.assertEqual(after.count('"V262_STATE n="'),1)
        self.assertEqual(before.count("v260_post_calls<=64u"),
                         after.count("v260_post_calls<=64u"))
        for term in ("ipc70_bus.write32(", "ipc70_ram.write8(",
                     "scheduler.service_one(", "ctx.mmu.write32("):
            self.assertEqual(before.count(term),after.count(term))
        for forbidden in ("ctx.pc=", "ctx.lr=", "ctx.gpr[3]=",
                          "ipc70_bus.write", "ipc70_ram.write",
                          "ctx.mmu.write","scheduler.service_one("):
            self.assertNotIn(forbidden,STATE_OBSERVER)
        self.assertIn("pending_native_ios_request()",STATE_OBSERVER)
        self.assertIn("queued_replies()",STATE_OBSERVER)
        with self.assertRaises(ValueError):
            derive("not the original-free harness")

    def test_16_trial_private_workflow_and_shell(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v262_ipc_state_harness.py",script)
        self.assertIn("V261_CALL_CENSUS verified=1",script)
        self.assertIn("V262_IPC_STATE verified=1",script)
        self.assertIn("analyze_v262_ipc_state.py",script)
        workflow=(HERE.parents[1]/".github/workflows/wii-v262-ipc-state.yml").read_text(encoding="utf-8")
        self.assertIn("grep -Fx 'V262_IPC_STATE verified=1'",workflow)
        self.assertIn("for n in $(seq 1 16); do",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as tmp:
            for title,body in (("generated",script),
                ("wrapper",(HERE/"run_v262_ipc_state.sh").read_text(encoding="utf-8"))):
                path=Path(tmp)/title
                path.write_text(body,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
