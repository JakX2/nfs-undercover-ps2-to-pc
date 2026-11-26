#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_formatter_fixture import merge,saved_slots,GUARD
class Fixture(unittest.TestCase):
    def test_merge(self):
        r=0x80001000;d=0x80002000;site=r+92
        ws=[0x60000000]*25;ws[23]=0x48000001|((d-site)&0x03fffffc)
        path=tuple(r+4*i for i in range(24) if i!=17)
        old={r:(ws[0],GUARD)}
        b=merge(old,r,ws,path,d,0x60000000)
        self.assertEqual(b[r][17],GUARD);self.assertEqual(b[d],(0x60000000,GUARD))
        with self.assertRaises(ValueError):merge(old,r,ws,path[:-1],d,0)
    def test_slots(self):
        mem={};sp=-160
        for at,reg in [(4,32)]+[(4*(i-32),i) for i in range(16,32)]:
            v=('lr',0) if reg==32 else ('reg',reg)
            for i in range(4):mem[sp+at+i]=('part',v,4,i)
        self.assertEqual(len(saved_slots(mem,sp,704)),17)
        bad=dict(mem);bad[sp-1]=('byte',0)
        with self.assertRaises(ValueError):saved_slots(bad,sp,704)
if __name__=='__main__':unittest.main(verbosity=2)
