#!/usr/bin/env python3
"""V245 synthetic AOT callback body-map fixture and private audit safeguards."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from audit_v245_generated_callback import SPANS, CALLS, scan, body_at, fixture_match, format_result
from derive_v245_sc_aot_map_runner import derive as runner, PATTERN, AUDIT
HERE=Path(__file__).resolve().parent

class V245(unittest.TestCase):
    def test_synthetic_compiler_output(self):
        source="""void callback(CPUContext& ctx) {
  if (nwii::runtime::g_trace_calls && ctx.pc == 0x804F0E04) nwii::runtime::trace_call(0x804F0E04, ctx);
loc_804F0E04: ;
  { ctx.gpr[1] = ea; } // stwu r1, -16(r1)
loc_804F0F50: ;
  ctx.lr = 0x804F0F54;
  ctx.pc = ctx.ctr; return;
loc_804F0F80: ;
}
void isfs(CPUContext& ctx) {
  if (nwii::runtime::g_trace_calls && ctx.pc == 0x804F1E2C) nwii::runtime::trace_call(0x804F1E2C, ctx);
loc_804F1E2C: ;
  { ctx.gpr[1] = ea; } // stwu r1, -32(r1)
loc_804F1E3C: ;
}
void nand(CPUContext& ctx) {
  if (nwii::runtime::g_trace_calls && ctx.pc == 0x8051E06C) nwii::runtime::trace_call(0x8051E06C, ctx);
}
static const X map[] = {{0x804F0E04, 0x804F0F84, callback},
                       {0x804F1E2C, 0x804F1EE4, isfs},
                       {0x8051E06C, 0x8051E0E4, nand}};
"""
        evidence=scan(source)
        self.assertTrue(all(evidence.values()))
        self.assertIn("loc_804f0f50",body_at(source,CALLS["cb"]))
        broken=source.replace("ctx.lr = 0x804F0F54;","ctx.lr = 0x805192AC;")
        self.assertFalse(scan(broken)["cb_link"])
        self.assertEqual(sum("0x804F0E04" in line for line in source.splitlines()),2)

    def test_private_dol_comparison_only_boolean(self):
        def read(blob,address,size):
            if address not in (x[0] for x in SPANS.values()):
                raise ValueError("unexpected span")
            return bytes([blob[0]])*size
        same=fixture_match(b"a",b"a",reader=read)
        changed=fixture_match(b"a",b"b",reader=read)
        self.assertTrue(all(same.values()))
        self.assertFalse(any(changed.values()))
        row=format_result(True,same,{k:True for k in scan("").keys()})
        self.assertIsNotNone(re.fullmatch(PATTERN,row))
        self.assertNotIn("raw=",row)
        self.assertNotIn("0x",row)

    def test_owner_runner_protects_private_generated_cpp(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("audit_v245_generated_callback.py",script)
        self.assertIn('> "$work/v245-aot.log" 2>&1',script)
        self.assertIn("V244_SC_CALLBACK_LINK verified=1",script)
        self.assertIn("V245_SC_AOT_MAP verified=1",script)
        self.assertIn("V245_STAGE entered=1",script)
        self.assertIn("V245_STAGE completed=1",script)
        self.assertIn("V245_STAGE failed=1",script)
        self.assertIn("V245_AOT_DIAG stage=record kind=mismatch",script)
        self.assertNotIn("cat $work",AUDIT)
        self.assertNotIn("source=",AUDIT)
        self.assertIn("V245_AOT_DIAG stage=", (HERE/"audit_v245_generated_callback.py").read_text())
        self.assertIn("V245_AOT_DIAG stage=",script)
        self.assertNotIn("traceback.print_exc", (HERE/"audit_v245_generated_callback.py").read_text())
        wf=(HERE.parents[1]/".github/workflows/wii-v245-sc-aot-map.yml").read_text()
        for marker in ("test_v245_sc_aot_map.py","run_v245_sc_aot_map.sh",
                       "V245_SC_AOT_MAP verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as tmp:
            for filename,contents in (("derived.sh",script),("wrapper.sh",(HERE/"run_v245_sc_aot_map.sh").read_text())):
                p=Path(tmp)/filename;p.write_text(contents,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
