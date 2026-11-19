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
        self.assertIn("make_start_to_sc_helper_v125.py",script)
        self.assertIn("test_v125_sc_helper_geometry.py",script)
        self.assertIn("V125_GEOMETRY_FAILURE code=[0-9]{1,2}",script)
        self.assertIn("V125_GEOMETRY_KIND import=1",script)
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
        self.assertIn("V125_GENERATED_TARGET present=[01]",s)
        self.assertIn("V125_GEOMETRY_KIND import=[01]",s)
        self.assertEqual(s.count("              grep -E '^V110_WRAPPER"),1)
        for f in ("run_v125_continuous_sc_helper.sh","diagnose_sc_helper_v125.py"):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,s)
        for f in ("make_start_to_sc_helper_v125.py","test_v125_sc_helper_geometry.py"):
            self.assertTrue((HERE/f).is_file());self.assertIn(f,runner((HERE/"run_v79_continuous_reply_entry.sh").read_text()))
        for m in ("V124_NEXT_CALL pc=8051e5bc","V125_NEXT_CALL pc=[0-9a-f]{8}",
                  "stage=125","WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,s)
if __name__=="__main__":unittest.main()
