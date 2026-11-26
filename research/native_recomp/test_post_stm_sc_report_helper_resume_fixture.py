#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_helper_resume_fixture import merge,GUARD,trace_resume_entry
class Fixture(unittest.TestCase):
    def test_merge(self):
        r=0x80001000;d=0x80002000;site=r+84
        ws=[0x60000000]*30;ws[21]=0x48000001|((d-site)&0x03fffffc)
        path=tuple(r+4*i for i in range(13,22) if i!=17)
        old={r:tuple(ws[:13])+(GUARD,)}
        b=merge(old,r,ws,path,site,d,0x60000000)
        self.assertEqual(b[r][17],GUARD);self.assertEqual(b[d],(0x60000000,GUARD))
        for bad in (path[:-1],(*path[:-1],path[-2])):
            with self.assertRaises(ValueError):merge(old,r,ws,bad,site,d,0)
    def test_trace_resume_entry(self):
        pc=0x80001034;w=0x2c030000
        s=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n    post_stm_sc_report_resume_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
        out=trace_resume_entry(s,pc,w)
        self.assertIn(f'ctx.pc == 0x{pc:X}',out)
        self.assertLess(out.index('trace_call'),out.index('++ctx.inst_count'))
        self.assertEqual(out.count('++ctx.inst_count'),1)
        for bad in (out,s+s,s.replace('++ctx.inst_count','--ctx.inst_count')):
            with self.assertRaises(ValueError):trace_resume_entry(bad,pc,w)
if __name__=='__main__':unittest.main(verbosity=2)
