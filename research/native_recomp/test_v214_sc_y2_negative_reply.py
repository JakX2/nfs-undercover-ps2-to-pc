#!/usr/bin/env python3
"""V214 source-only negative IOS reply transport verification."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v208_sc_y2_reply_publication_harness import derive as previous, PUBLISH as PREVIOUS_PUBLISH, NEXT_END as PREVIOUS_END
from derive_v214_sc_y2_negative_reply_harness import derive, STOP, VERIFY, NEXT_END
from derive_v214_sc_y2_negative_reply_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V214(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_negative_open_reply_without_forged_descriptor(self):
        self.assertIn(STOP,PREVIOUS_PUBLISH)
        self.assertNotIn(STOP,self.after)
        self.assertIn(VERIFY,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        # Preserve the V208 terminal reply-state definition. Previously
        # replacing the whole block left the later 'done' undeclared.
        self.assertIn("const bool done=",self.after)
        self.assertIn("const bool done=",PREVIOUS_END)
        self.assertIn("done&&!c.is_running",NEXT_END)
        self.assertNotIn("V208 original second IOS reply native publication checkpoint failed",self.after)
        for token in ("int32_t(fd)==S::Invalid","!opened",
                      "ipc70_ram.read32(req+16u)>3u",
                      "ipc70_ram.read32(req+12u)!=0u",
                      "step&&wire&&signal&&drained&&cpu&&sc_before",
                      "++v214_negative_seen"):
            self.assertIn(token,VERIFY)
        self.assertIn("v214_negative_seen==1u",NEXT_END)
        self.assertNotIn("V208_Y2_ALIAS",self.after)
        self.assertIn("V208_Y2_PATHCLASS",self.after)
        with self.assertRaises(ValueError):derive("unmatched base")

    def test_preserves_native_service_and_cpu_state(self):
        for token in ("scheduler.service_one(","ipc70_bus.tick(",
                      "ipc70_ram.write8(","ctx.mmu.write32(",
                      "ipc70_bus.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write",
                    "service_one(","ipc70_bus.tick(","ctx.gpr[3]="):
            self.assertNotIn(bad,VERIFY+NEXT_END)
        self.assertIn('check(cpu,"V208 second IOS service unexpectedly modified guest CPU");',self.after)

    def test_16_trials_and_bounded_diagnostics(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("derive_v214_sc_y2_negative_reply_harness.py",
                  "V207_SC_Y2_HELPER_NEXT verified=1",
                  "V214_SC_Y2_NEGATIVE verified=1"):
            self.assertIn(m,script)
        good="V214_Y2_NEGATIVE invalid=1 mode=1 path=1 published=1 irq=1 drained=1 cpu=1 sc=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("irq=1","irq=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("invalid=1","invalid=0")))

        from diagnose_v214_native_failure import diagnose
        public='check(false,"V82 scheduler did not set default thread context");'
        private='what(): V82 scheduler did not set default thread context'
        self.assertEqual(diagnose(private,public),
            "V214_NATIVE_DIAG public=1 kind=v82_context trials=0 negative=0")
        self.assertEqual(diagnose("what(): PRIVATE_UNRELATED",public),
            "V214_NATIVE_DIAG public=0 kind=unmatched trials=0 negative=0")
        log=("V79_TRIAL_PASS trial=0\n"
             "V214_Y2_NEGATIVE invalid=1 mode=1 path=1 published=1 "
             "irq=1 drained=1 cpu=1 sc=1\n"
             "what(): V82 scheduler did not set default thread context")
        self.assertEqual(diagnose(log,public),
            "V214_NATIVE_DIAG public=1 kind=v82_context trials=1 negative=1")
        self.assertIn("diagnose_v214_native_failure.py",script)
        from diagnose_v214_compile_failure import diagnose as compile_diagnose
        sample=("harness.cpp:10067:12: error: 'v214_negative_seen' was not declared in this scope\\n"
                "harness.cpp:10068:12: note: did you mean something else")
        self.assertEqual(compile_diagnose(sample,"harness"),
            "V214_COMPILE_DIAG unit=harness kind=undeclared line=10067 symbol=v214_state")
        self.assertEqual(compile_diagnose("PRIVATE_COMPILER_DATA","harness"),
            "V214_COMPILE_DIAG unit=harness kind=no_public_error line=0 symbol=other")
        self.assertIn("diagnose_v214_compile_failure.py",script)

        wf=(HERE.parents[1]/".github/workflows/wii-v214-sc-y2-negative-reply.yml").read_text()
        for m in ("run_v214_sc_y2_negative_reply.sh",
                  "test_v214_sc_y2_negative_reply.py",
                  "V214_SC_Y2_NEGATIVE verified=1"):
            self.assertIn(m,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,src in (("runner",script),("wrapper",(HERE/"run_v214_sc_y2_negative_reply.sh").read_text())):
                p=Path(d)/name;p.write_text(src,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
