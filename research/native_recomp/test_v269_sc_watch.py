#!/usr/bin/env python3
"""V269 synthetic MMU pre-store trace and source-only native derivation guards."""
import subprocess
import unittest
from pathlib import Path
from analyze_v269_sc_write import parse,summarize
from derive_v269_sc_write_harness import patch,GLOBAL,WATCH,ARM,RESET,FRONTIER,WATCHER
from derive_v269_sc_write_runner import patch as runner_patch, OLD, DONE

HERE=Path(__file__).resolve().parent
END="V260_CALL_FRONTIER guest=1 coherent=1 mapped=1 calls=64 sc=1 pc=805265d4 lr=8052f92c"

def sample(with_events=True):
    lines=[]
    for _ in range(16):
        if with_events:
            lines.extend((
                "V269_SC_WRITE n=1 before=1 next=0 width=8 guest=1 inst=101",
                "V269_SC_WRITE n=2 before=0 next=1 width=8 guest=1 inst=131"))
        lines.append(END)
    return "\n".join(lines)

class Tests(unittest.TestCase):
    def test_realistic_synthetic_write_transitions(self):
        trials=parse(sample())
        self.assertEqual(len(trials),16)
        report=summarize(trials)
        self.assertIn("events=32 min_trial=2 max_trial=2 changed=32",report)
        self.assertIn("write_zero=16 write_one=16 write_other=0",report)
        self.assertIn("one_to_one=0 one_to_zero=16",report)
        self.assertIn("events=0 min_trial=0 max_trial=0",summarize(parse(sample(False))))

    def test_error_paths_fail_closed(self):
        cases=(
            (sample().replace("V269_SC_WRITE n=2 ","V269_SC_WRITE n=3 ",1),"wrong_order"),
            (sample().replace("before=1 next=0","before=256 next=0",1),"invalid_byte"),
            (sample().replace("guest=1 inst=101","guest=0 inst=101",1),"invalid_guest"),
            (sample().replace("guest=1 inst=131","guest=1 inst=90",1),"instruction_regression"),
            ("\n".join(sample().splitlines()[:-1]),"wrong_trials"),
        )
        for data,reason in cases:
            with self.subTest(reason=reason),self.assertRaisesRegex(ValueError,reason):
                parse(data)

    def test_instrumentation_read_only_and_exact(self):
        template="\n".join((GLOBAL,WATCH,ARM,RESET,FRONTIER))
        result=patch(template)
        self.assertIn(WATCHER,result)
        self.assertIn("g_watch_addr=scaddr;",result)
        self.assertIn("g_watch_addr=0u;v269_watch_armed=false;",result)
        for forbidden in ("cpu->mmu.write","cpu->gpr[3]=","cpu->msr=",
                          "ipc70_bus.write","ipc70_ram.write"):
            self.assertNotIn(forbidden,WATCHER)
        with self.assertRaises(ValueError):
            patch("no original-free harness anchors")
        self.assertIn("analyze_v269_sc_write.py",runner_patch(OLD+"\n"+DONE))
        with self.assertRaises(ValueError):
            runner_patch("no previous native runner")

    def test_private_ci_guards(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v269-sc-watch.yml").read_text(encoding="utf-8")
        self.assertIn("V269_SC_WATCH verified=1",wf)
        self.assertIn("for n in $(seq 1 16); do",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        subprocess.run(["bash","-n",str(HERE/"run_v269_sc_watch.sh")],check=True)

if __name__=="__main__":
    unittest.main()
