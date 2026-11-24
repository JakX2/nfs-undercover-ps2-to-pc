#!/usr/bin/env python3
import unittest
from dataclasses import replace
from repair_v424_nand_aot_placeholder import aot_entry,prepare,result
from test_v420_nand_sc_provenance import make_trial,encode
from test_v414_nand_resumed_coverage import dol,BODY,A,B,C,NOP

def cpp(pc):
    return f'void func_{pc:08X}(CPUContext& ctx) {{\n    nwii::runtime::trace_call(0x{pc:08X}, ctx);\n}}\n{{0x{pc:08X}, 0x{pc+16:08X}, func_{pc:08X}}},\n'
class Tests(unittest.TestCase):
    def test_exact_restore_without_live_text(self):
        owner=dol(BODY*3);fixture=dol(BODY+NOP*4+BODY)
        t=tuple(replace(e,ew=0,lw=0) for e in make_trial())
        plan=prepare(owner,fixture,{A:16,B:16,C:16},cpp(B),[t]*16)
        self.assertEqual(plan.candidate,owner);self.assertEqual(plan.reason,'ready')
        self.assertNotIn(f'{B:08x}',plan.row())
    def test_interior_tail_preserves_parent(self):
        owner=dol(BODY*3);fixture=dol(BODY+BODY[:4]+NOP*3+BODY)
        t=tuple(replace(e,pc=B+4) if e.pc==B else e for e in make_trial())
        plan=prepare(owner,fixture,{A:16,B:16,C:16},cpp(B+4),[t]*16)
        self.assertEqual(plan.kind,'interior');self.assertEqual(plan.size,12);self.assertEqual(plan.candidate,owner)
    def test_missing_dispatch_or_ambiguous_route(self):
        owner=dol(BODY*3);fixture=dol(BODY+NOP*4+BODY);t=make_trial();sizes={A:16,B:16,C:16}
        for src in (cpp(B).replace(f'func_{B:08X}}}', 'other}'),cpp(B)+cpp(B),cpp(C)):
            self.assertIsNone(prepare(owner,fixture,sizes,src,[t]*16).candidate)
        t2=tuple(replace(e,pc=C) if e.pc==B else e for e in t)
        self.assertIsNone(prepare(owner,fixture,sizes,cpp(B),[t]*15+[t2]).candidate)
    def test_mixed_not_repaired(self):
        owner=dol(BODY*3);fixture=dol(BODY+NOP*3+BODY[-4:]+BODY)
        self.assertIsNone(prepare(owner,fixture,{A:16,B:16,C:16},cpp(B),[make_trial()]*16).candidate)
    def test_partial_candidate_result(self):
        t=make_trial();raw=encode(t);row=result(raw*16,0,B)
        self.assertIn('trials=16 complete=16 target_seen=16 resumed=16 status3=0 same_retry=16 max_calls=192',row)
        prefix=b'\n'.join(raw.splitlines()[:5])+b'\n';row=result(prefix,134,B)
        self.assertIn('kind=signal trials=1 complete=0 target_seen=1 resumed=0',row)
        with self.assertRaises(ValueError):result(prefix.replace(b'call=2 ',b'call=3 ',1),134,B)
        self.assertNotIn(f'{B:08x}',row)
if __name__=='__main__':unittest.main()
