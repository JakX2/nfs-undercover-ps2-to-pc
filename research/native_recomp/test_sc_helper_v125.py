#!/usr/bin/env python3
"""V125 owner-free original SC continuation regression."""
from pathlib import Path
import unittest,subprocess,tempfile
from derive_v124_sc_second_save_harness import derive as previous
from derive_v125_sc_helper_harness import derive,EDITS
from derive_v125_sc_helper_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V125(unittest.TestCase):
    def test_harness(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src);actual=derive(src);expected=old
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:95]);expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected);self.assertEqual(actual,derive(src))
        for m in ("V125_NEXT_CALL pc=","addr==0x8051e5bcu&&ctx.lr==0x8051e054u",
                  "post125_next==1u&&nwii::runtime::post124_next==1u",
                  "nwii::runtime::post90_target==nwii::runtime::post125_pc&&"):
            self.assertIn(m,actual)
        for m in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(m),old.count(m))
    def test_runtime_shape(self):
        from classify_v125_runtime_shape import format_report
        text="terminate called after throwing an instance of std::runtime_error\n  what(): unsupported instruction"
        value=format_report(text)
        self.assertIn("exception=1",value)
        self.assertIn("missing=1",value)
        self.assertIn("lookup=0",value)
        self.assertIn("lookup=1",format_report("what(): unordered_map::at"))
        self.assertIn("fault=0",value)
        self.assertNotIn("unsupported instruction",value)
        self.assertIn("dispatch=0",format_report("V110_IPC_GATE dispatch=1"))
        self.assertIn("dispatch=1",format_report("what(): invalid indirect branch"))
        self.assertIn("runtime=1",format_report("terminate called after throwing an instance of 'std::runtime_error'"))

    def test_generator_assertion_catalog_uses_generator_source(self):
        from describe_v125_generator_assertion import describe,messages
        from classify_v67_generator_failure import classify
        from derive_v125_sc_helper_generator import derive as generated
        source=generated((HERE/"generate_start_to_ipc_ack_v77.cpp").read_text())
        labels=messages()
        self.assertGreater(len(labels),80)
        self.assertEqual(describe(80),labels[79])
        self.assertEqual(classify(source,"V67 generator: "+labels[79]),80)
        wf=(HERE.parents[1]/".github/workflows/wii-v125-sc-helper.yml").read_text()
        self.assertIn("describe_v125_generator_assertion.py",wf)
        self.assertIn("V104_STAGE generator_compiled",wf)
    def test_generator_branch_trace_preserves_guard(self):
        from derive_v125_sc_helper_generator import derive as generator
        from derive_v125_sc_helper_generator import OLD,NEW
        from derive_v104_sc_async_submit_generator import derive as previous_generator
        base=(HERE/"generate_start_to_ipc_ack_v77.cpp").read_text()
        old=previous_generator(base)
        self.assertEqual(old.count(OLD),1)
        actual=generator(base)
        self.assertEqual(actual,old.replace(OLD,NEW,1))
        self.assertIn('V125_BAD_BRANCH site=',actual)
        self.assertIn('require((ins>>26)==18 && (ins&3)==1,"expected absolute-free PPC BL");',actual)
        self.assertIn("derive_v125_sc_helper_generator.py",runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
    def test_generated_target_diagnostic(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("V125_GENERATED_TARGET present=1",s)
        self.assertIn("V125_GENERATED_TARGET present=0",s)
        self.assertIn("func_8051[eE]5[bB][cC]",s)
    def test_exception_site(self):
        derived=derive((HERE/"test_start_to_ipc_ack_v77.cpp").read_text())
        self.assertIn("V125_EXCEPTION_SITE pc=",derived)
        self.assertIn("post125_enter_inst=ctx.inst_count",derived)
        self.assertIn("V125_EXCEPTION_STEPS delta=",derived)
        self.assertIn("V125_EXCEPTION_STEPS delta=[0-9]{1,6}",runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
        self.assertIn("dynamic_cast<const std::runtime_error*>(&e)",derived)
        self.assertIn("V125_EXCEPTION_SITE pc=[0-9a-f]{8}",runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
    def test_bounded_call_trace(self):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        derived=derive(source)
        self.assertIn("V125_TRACE_CALL seq=",derived)
        self.assertIn("V125_OPCODE_CLASS first_branch=",derived)
        self.assertIn("V125_OPCODE_DETAIL major0=",derived)
        self.assertIn("V125_OPCODE_DETAIL major0=[0-9]{1,2}",runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
        self.assertIn("post125_trace_count<8u",derived)
        self.assertIn("post123_next==1u&&addr==0x8051e5bcu&&ctx.lr==0x8051e054u",derived)
        self.assertIn("V125_TRACE_CALL seq=[0-9]{1,2}",runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
    def test_fixture_coverage_boolean_only(self):
        import struct
        from diagnose_v125_fixture_coverage import PC,inspect,render
        raw=bytearray(264)
        struct.pack_into(">III",raw,0,256,0x8051E5BC,8)
        # DOL text offset, guest address, and size occupy independent columns.
        struct.pack_into(">I",raw,0,256)
        struct.pack_into(">I",raw,0x48,PC)
        struct.pack_into(">I",raw,0x90,8)
        raw[256:264]=struct.pack(">II",0x60000000,0x60000000)
        earlier=bytes(raw)
        raw[256:264]=struct.pack(">II",0x7c0802a6,0x60000000)
        output=render(inspect(earlier,bytes(raw)))
        self.assertIn("mapped=1 owner=1 zero=0 nop=1 same=0",output)
        self.assertNotIn("7c0802a6",output)
        self.assertIn("diagnose_v125_fixture_coverage.py",runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
    def test_fixture_builder_placeholder_bounds(self):
        import struct
        from make_start_to_sc_helper_v125 import ENTRY,extent,NOP_WORD,MAX_SPAN,MIN_SPAN
        from make_start_to_irq_enable_v68 import replace as patch
        raw=bytearray(256+0x80)
        struct.pack_into(">I",raw,0,256)
        struct.pack_into(">I",raw,0x48,ENTRY)
        struct.pack_into(">I",raw,0x90,0x80)
        raw[256:256+0x80]=NOP_WORD*(0x80//4)
        raw[256+0x40:256+0x44]=struct.pack(">I",0x4E800020)
        self.assertEqual(extent(raw),0x40)
        patch(raw,ENTRY,NOP_WORD*(0x40//4),struct.pack(">I",0x7c0802a6)*(0x40//4))
        with self.assertRaises(ValueError):
            extent(raw)
        self.assertTrue(MAX_SPAN>=MIN_SPAN>=0x20)
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("make_start_to_ipc_ack_v77.py",script)
        self.assertIn("test_v77_continuous_ipc_ack_geometry.py",script)
        self.assertNotIn('python3 "$here/test_v77_continuous_ipc_ack_geometry.py"',script)
        self.assertLess(script.index("V125_STAGE_CHECK before_geometry=1"),
                        script.index('python3 "$here/test_v125_sc_helper_geometry.py"'))

        self.assertIn("V125_GEOMETRY_FAILURE code=[0-9]{1,2}",script)
        self.assertIn("V125_GEOMETRY_KIND import=1",script)
        self.assertIn("V125_STAGE_CHECK geometry_failure_branch=1",script)
        self.assertIn("if python3 \"$here/test_v125_sc_helper_geometry.py\"",script)
        self.assertIn("V125_GEOMETRY_STATUS ok=1",script)
        self.assertIn("V125_GEOMETRY_STATUS ok=0",script)
        self.assertEqual(script.count("V125_GEOMETRY_STATUS ok=0"),1)

        for marker in ("V125_STAGE_CHECK after_probe=1","V125_STAGE_CHECK before_geometry=1","V125_STAGE_CHECK after_geometry=1"):
            self.assertIn(marker,script)
        self.assertIn("restore_sc_helper_late_v125.py",script)
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "V124_NEXT_CALL pc=8051e5bc lr=8051e054","stage=125"):
            self.assertIn(m,s)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
    def test_workflow(self):
        s=(HERE.parents[1]/".github/workflows/wii-v125-sc-helper.yml").read_text()
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)
        self.assertTrue(s.rstrip().endswith('rm -rf -- "$RUNNER_TEMP/nwii" "$RUNNER_TEMP/originals" "$RUNNER_TEMP/sc125.log"'))
        self.assertIn("V125_GENERATED_TARGET present=[01]",s)
        self.assertIn("V125_GEOMETRY_KIND import=[01]",s)
        self.assertIn("verify_v125_owner_fixture.py",s)
        self.assertIn("grep -Fx 'V110_WRAPPER derived'",s)
        self.assertIn("grep -Fx 'V110_WRAPPER syntax_ok'",s)
        self.assertEqual(s.count("      - name: Remove private owner and generated code"),1)
        for f in ("run_v125_continuous_sc_helper.sh","diagnose_sc_helper_v125.py"):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,s)
        for f in ("restore_sc_helper_late_v125.py",):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
        for m in ("V124_NEXT_CALL pc=8051e5bc","V125_NEXT_CALL pc=[0-9a-f]{8}",
                  "stage=125","WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,s)
    def test_derivation_failure_is_bounded_and_private(self):
        import os
        wrapper=(HERE/"run_v125_continuous_sc_helper.sh").read_text()
        workflow=(HERE.parents[1]/".github/workflows/wii-v125-sc-helper.yml").read_text()
        self.assertIn("V125_DERIVATION result=failed kind=",wrapper)
        self.assertIn("V125_DERIVATION result=failed kind=",workflow)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"run_v125_continuous_sc_helper.sh").write_text(wrapper)
            (root/"run_v79_continuous_reply_entry.sh").write_text("synthetic input")
            (root/"derive_v125_sc_helper_runner.py").write_text(
                "raise ValueError('V125 runner missing source anchor: SECRET_SENTINEL')\n")
            proc=subprocess.run(
                ["bash",str(root/"run_v125_continuous_sc_helper.sh"),"unused","unused"],
                capture_output=True,text=True,timeout=10)
            self.assertEqual(proc.returncode,1)
            self.assertEqual(proc.stdout,"")
            self.assertEqual(proc.stderr.strip(),
                             "V125_DERIVATION result=failed kind=missing_anchor")
            self.assertNotIn("SECRET_SENTINEL",proc.stderr)

if __name__=="__main__":unittest.main()
