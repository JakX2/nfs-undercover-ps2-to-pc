#!/usr/bin/env python3
"""V261 original-free 64-call census, parse and privacy regressions."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v260_ipc_ppcmsg_boundary_harness import derive as previous
from derive_v261_guest_call_census_harness import derive, INSTRUMENTED
from derive_v261_guest_call_census_runner import derive as runner
from analyze_v261_postipc_calls import parse_trials, summarize, census

HERE = Path(__file__).resolve().parent


def fixture():
    entries = []
    for _ in range(16):
        for n in range(1, 65):
            pc = 0x805265D4 if n == 64 else 0x80521000 + 4 * (n % 8)
            lr = 0x8052F92C if n == 64 else 0x80522000 + 4 * (n % 8)
            entries.append(f"V261_CALL n={n} pc={pc:08x} lr={lr:08x} inst={n * 11}")
    return "\n".join(entries)


class V261(unittest.TestCase):
    def test_synthetic_census_and_fail_closed_edges(self):
        sample = fixture()
        blocks = parse_trials(sample)
        self.assertEqual(len(blocks), 16)
        statistics = census(blocks[0])
        self.assertEqual(statistics["unique_pairs"], 9)
        self.assertEqual(statistics["repeated"], 55)
        self.assertEqual(statistics["new_second"], 1)
        self.assertEqual(statistics["match32"], 31)
        self.assertIn("stable=1 distinct=1", summarize(blocks))
        self.assertIn("last_pc=805265d4 last_lr=8052f92c", summarize(blocks))
        cases = (
            (sample.replace("V261_CALL n=16 ", "V261_CALL n=17 ", 1), "nonsequential_call_marker"),
            (sample.replace("inst=187", "inst=1", 1), "nonmonotonic_instruction_counter"),
            (sample.replace("pc=805265d4 lr=8052f92c", "pc=805265d8 lr=8052f92c", 1), "unverified_frontier"),
            ("\n".join(sample.splitlines()[:-1]), "incomplete_call_trace"),
            (sample + "\nV261_CALL n=1 pc=12345678 lr=abcdef01 inst=1", "incomplete_call_trace"),
        )
        for bad, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                parse_trials(bad)

    def test_original_guest_only_and_no_extra_budget(self):
        raw = (HERE / "test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        before = previous(base(raw))
        after = derive(base(raw))
        self.assertEqual(after.count('"V261_CALL n="'), 1)
        self.assertIn(INSTRUMENTED, after)
        self.assertEqual(after.count("v260_post_calls<=64u"), before.count("v260_post_calls<=64u") + 1)
        self.assertEqual(after.count("ipc70_bus.write32("), before.count("ipc70_bus.write32("))
        self.assertEqual(after.count("cpu->is_running=false;throw ExceptionStop{}"),
                         before.count("cpu->is_running=false;throw ExceptionStop{}"))
        for forbidden in ("ctx.pc=", "ctx.lr=", "ctx.gpr[", "ctx.mmu.write",
                          "ipc70_bus.write", "ipc70_ram.write", "scheduler.service_one"):
            self.assertNotIn(forbidden, INSTRUMENTED)
        with self.assertRaises(ValueError):
            derive("no original-free native source")

    def test_runner_workflow_and_shell(self):
        s = runner((HERE / "run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        self.assertIn("derive_v261_guest_call_census_harness.py", s)
        self.assertIn("analyze_v261_postipc_calls.py", s)
        self.assertIn("V261_CALL_CENSUS verified=1", s)
        self.assertIn("V260_POSTIPC_RESULT kind=calls trials=16", s)
        self.assertNotIn('python3 "$V110_SOURCE_ROOT/derive_v260_ipc_ppcmsg_boundary_harness.py"', s)
        wf = (HERE.parents[1] / ".github/workflows/wii-v261-guest-call-census.yml").read_text(encoding="utf-8")
        self.assertIn("grep -Fx 'V261_CALL_CENSUS verified=1'", wf)
        self.assertIn("for n in $(seq 1 16); do", wf)
        self.assertNotIn("upload-artifact", wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"), 1)
        with tempfile.TemporaryDirectory() as td:
            for title, body in (("runner", s),
                                ("wrapper", (HERE / "run_v261_guest_call_census.sh").read_text(encoding="utf-8"))):
                file = Path(td) / title
                file.write_text(body, encoding="utf-8")
                subprocess.run(["bash", "-n", str(file)], check=True)


if __name__ == "__main__":
    unittest.main()
