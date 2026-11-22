#!/usr/bin/env python3
"""V263 source-only regression: bounded callsite recurrence and EE correlation."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from analyze_v263_hotspot import analyze
from derive_v263_hotspot_runner import derive as derive_runner
HERE = Path(__file__).resolve().parent

def fixture() -> str:
    """Independent 16x64 original-free CPU and IRQ trace fixtures."""
    call_lines = []
    state_lines = []
    for _ in range(16):
        for n in range(1,65):
            pc = 0x805265D4 if n == 64 else 0x80521000 + 4*(n%8)
            lr = 0x8052F92C if n == 64 else 0x80522000 + 4*(n%8)
            call_lines.append(
                f"V261_CALL n={n} pc={pc:08x} lr={lr:08x} inst={n*11}")
            state_lines.append(
                f"V262_STATE n={n} mapped=1 ee={int(n%2==0)} irq=0 "
                "native_request=0 queued=0 sc=1 reply=1")
    return "\n".join(call_lines + state_lines)


class V263(unittest.TestCase):
    def test_synthetic_hotspots_and_host_independence(self):
        total, ranks = analyze(fixture())
        self.assertIn("trials=16 calls=64 stable=1", total)
        self.assertIn("unique_pairs=9 max_freq=8 restore_hits=1", total)
        self.assertIn("irq_ever=0 request_ever=0 sc_stable=1", total)
        self.assertEqual(len(ranks), 3)
        self.assertTrue(all(r.startswith(f"V263_PAIR rank={i} ")
                            for i, r in enumerate(ranks, 1)))
        self.assertIn("first32=4 last32=4", ranks[0])
        # Synthetic traces intentionally have strictly increasing counts;
        # this does not imply that the real game can complete startup.
        self.assertIn("gap_min=", ranks[0])
        self.assertIn("ee_on=", ranks[0])

    def test_reject_forged_or_incomplete_windows(self):
        source = fixture()
        cases = [
            (source.replace("V261_CALL n=2 ", "V261_CALL n=3 ", 1),
             "nonsequential_call_marker"),
            (source.replace("V262_STATE n=2 ", "V262_STATE n=3 ", 1),
             "out_of_order_state"),
            (source.replace("V261_CALL n=4 pc=80521010",
                            "V261_CALL n=4 pc=80521014", 1),
             "unstable_guest_calls"),
            (source.replace("V262_STATE n=1 mapped=1 ee=0 irq=0",
                            "V262_STATE n=1 mapped=1 ee=1 irq=0", 1),
             "unstable_ios_state"),
        ]
        for altered, marker in cases:
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(ValueError, marker):
                    analyze(altered)

    def test_runner_and_private_workflow(self):
        source = (HERE/"run_v79_continuous_reply_entry.sh").read_text(
            encoding="utf-8")
        derived = derive_runner(source)
        self.assertIn("derive_v262_ipc_state_harness.py", derived)
        self.assertIn("analyze_v262_ipc_state.py", derived)
        self.assertIn("analyze_v263_hotspot.py", derived)
        self.assertIn("V263_HOTSPOT verified=1", derived)
        self.assertNotIn("ctx.gpr[3]=", derived)
        wf = (HERE.parents[1]/".github/workflows/wii-v263-hotspot.yml").read_text(
            encoding="utf-8")
        self.assertIn("grep -Fx 'V263_HOTSPOT verified=1'", wf)
        self.assertIn("V263_PAIR rank=", wf)
        self.assertIn("for n in $(seq 1 16); do", wf)
        self.assertNotIn("upload-artifact", wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"), 1)
        with tempfile.TemporaryDirectory() as td:
            for name, body in (
                ("runner", derived),
                ("wrapper", (HERE/"run_v263_hotspot.sh").read_text(encoding="utf-8")),
            ):
                path = Path(td)/name
                path.write_text(body, encoding="utf-8")
                subprocess.run(["bash", "-n", str(path)], check=True)

    def test_strict_inherited_anchors(self):
        with self.assertRaises(ValueError):
            derive_runner("not a native owner-original Wii script")


if __name__ == "__main__":
    unittest.main()
