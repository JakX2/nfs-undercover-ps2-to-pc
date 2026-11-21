#!/usr/bin/env python3
"""Source-only verification of V225 AOT indirect callback root and isolation."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v79_reply_generator import derive as previous_generator
from derive_v225_isfs_callback_generator import derive as generator, OLD, NEW, ASSERT
from derive_v225_isfs_callback_runner import derive as runner, PROBE
HERE=Path(__file__).resolve().parent

class V225(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(HERE/"generate_start_to_ipc_ack_v77.cpp").read_text()
        cls.base=previous_generator(cls.raw)
        cls.with_root=generator(cls.raw)

    def test_only_add_indirect_callback_root(self):
        self.assertEqual(self.base.count(OLD),1)
        self.assertEqual(self.with_root.count(NEW),1)
        self.assertNotIn(OLD,self.with_root)
        self.assertIn(ASSERT,self.with_root)
        self.assertEqual(self.base.count("const auto& funcs=analyzer.get_functions();"),1)
        self.assertIn("funcs.count(0x804f0e04u)==1u",self.with_root)
        self.assertEqual(self.with_root.count("analyzer.analyze("),self.base.count("analyzer.analyze("))
        self.assertEqual(self.with_root.count("exe.sections.push_back("),self.base.count("exe.sections.push_back("))
        with self.assertRaises(ValueError):generator("not an authenticated source")

    def test_owner_runner_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v225_isfs_callback_generator.py",script)
        self.assertIn("V225_CB_AOT_ROOT verified=1",script)
        self.assertIn("V225_SC_ISFS_CALLBACK_AOT verified=1",script)
        self.assertIn("V177_SC_REPLY_NEXT verified=1",script)
        self.assertNotIn('echo "$(cat "$work/generation.log")"',script)
        self.assertIsNotNone(re.fullmatch(PROBE,"V225_CB_ANALYZER rooted=1 analyzed=1"))
        wf=(HERE.parents[1]/".github/workflows/wii-v225-isfs-callback-aot.yml").read_text()
        for mark in ("run_v225_isfs_callback_aot.sh",
                     "test_v225_isfs_callback_aot.py",
                     "V225_SC_ISFS_CALLBACK_AOT verified=1"):
            self.assertIn(mark,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,content in (("generated",script),("wrapper",(HERE/"run_v225_isfs_callback_aot.sh").read_text())):
                p=Path(d)/name;p.write_text(content)
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
