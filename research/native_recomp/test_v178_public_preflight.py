#!/usr/bin/env python3
"""Original-free regression guards for V178 owner's preflight diagnostics."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from instrument_v178_public_preflight import derive, STEPS
from derive_v178_sc_reply_burst_runner import derive as derive_runner

HERE=Path(__file__).resolve().parent
BASE=HERE/"run_v79_continuous_reply_entry.sh"


class PublicPreflightTests(unittest.TestCase):
    def test_markers_preserve_every_public_command_verbatim(self):
        source=BASE.read_text(encoding="utf-8")
        marked=derive(source)
        self.assertEqual(len(STEPS),19)
        self.assertEqual(len({step for step,_ in STEPS}),len(STEPS))
        for step,command in STEPS:
            self.assertEqual(source.splitlines().count(command),1,step)
            self.assertEqual(marked.splitlines().count(command),1,step)
            self.assertEqual(
                marked.count(f"echo 'V178_PREFLIGHT enter={step}'\n{command}"),1,step)
        self.assertEqual(marked.count("V178_PREFLIGHT enter="),len(STEPS))
        with tempfile.TemporaryDirectory() as td:
            script=Path(td)/"public.sh"
            script.write_text(marked,encoding="utf-8")
            subprocess.run(["bash","-n",str(script)],check=True)

    def test_whole_v178_inherited_runner_keeps_private_cleanup(self):
        source=BASE.read_text(encoding="utf-8")
        script=derive_runner(source)
        for step,command in STEPS:
            self.assertIn(f"echo 'V178_PREFLIGHT enter={step}'\n{command}",script)
        self.assertIn("derive_v178_sc_reply_burst_harness.py",script)
        self.assertIn("V178_SC_BURST verified=1",script)
        self.assertIn('trap \'rm -rf -- "$work"\' EXIT',script)
        self.assertEqual(script.count("V178_PREFLIGHT enter="),len(STEPS))

    def test_fail_closed_on_missing_or_ambiguous_step(self):
        source=BASE.read_text(encoding="utf-8")
        first=STEPS[0][1]
        with self.assertRaises(ValueError):derive(source.replace(first,"",1))
        with self.assertRaises(ValueError):derive(source+"\n"+first+"\n")
        with self.assertRaises(ValueError):derive(derive(source))

    def test_markers_never_contain_private_data_or_addresses(self):
        source=BASE.read_text(encoding="utf-8")
        script=derive(source)
        public_markers=[line for line in script.splitlines()
                        if line.startswith("echo 'V178_PREFLIGHT enter=")]
        self.assertEqual(len(public_markers),19)
        for marker in public_markers:
            self.assertNotIn("$owner",marker)
            self.assertNotIn("$root",marker)
            self.assertNotIn("secret",marker.lower())
            self.assertLess(len(marker),70)

if __name__=="__main__":
    unittest.main()
