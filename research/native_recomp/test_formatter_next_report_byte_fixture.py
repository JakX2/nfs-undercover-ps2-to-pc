#!/usr/bin/env python3
"""Original-free regressions for the guarded callee byte fixture."""
import unittest
from guarded_continuation import GUARD
from prepare_formatter_next_report_byte_fixture import render_report_byte, expand_report_byte

P=0x80010000
T=P-0x100
C=P+8
BL=0x48000001 | ((T-C)&0x03fffffc)
LBZ=(34<<26)|(9<<21)|(7<<16)|1
INTEGER=(14<<26)|(8<<21)|(8<<16)|1


class ReportByteFixture(unittest.TestCase):
    def setUp(self):
        self.old={P:(GUARD,GUARD,BL,GUARD),T:(LBZ,GUARD)}
        self.caller=(P,16,C,BL,T,LBZ,C+4)
        self.info=(T,LBZ,753,17,0x5a,T+4,INTEGER,C+4)
        self.new={**self.old,T:(LBZ,INTEGER,GUARD)}

    def next(self):
        return self.old,self.caller

    def contract(self):
        return self.new,self.info

    def probe(self):
        return expand_report_byte(self.old,self.next(),self.contract())

    def test_exact(self):
        self.assertEqual(self.probe(),self.new)
        out=render_report_byte(self.contract())
        self.assertIn('formatter_next_report_byte_private',out)
        self.assertIn('next_pc=',out)

    def test_indexed(self):
        word=(31<<26)|(9<<21)|(7<<16)|(8<<11)|(87<<1)
        self.old[T]=(word,GUARD)
        self.caller=(*self.caller[:5],word,self.caller[-1])
        self.info=(T,word,*self.info[2:])
        self.new[T]=(word,INTEGER,GUARD)
        self.assertEqual(self.probe(),self.new)

    def test_update_refused(self):
        self.info=(T,(35<<26)|(9<<21)|(7<<16)|1,*self.info[2:])
        with self.assertRaisesRegex(ValueError,'contract'):self.probe()

    def test_destination_refused(self):
        self.info=(T,(34<<26)|(13<<21)|(7<<16)|1,*self.info[2:])
        with self.assertRaisesRegex(ValueError,'contract'):self.probe()

    def test_byte_value_refused(self):
        for v in (-1,256,True):
            self.info=(*self.info[:4],v,*self.info[5:])
            with self.assertRaisesRegex(ValueError,'contract'):self.probe()

    def test_parent_range_refused(self):
        for at in (703,2049,True):
            self.info=(*self.info[:2],at,*self.info[3:])
            with self.assertRaisesRegex(ValueError,'contract'):self.probe()

    def test_report_range_refused(self):
        for at in (7,513,True):
            self.info=(*self.info[:3],at,*self.info[4:])
            with self.assertRaisesRegex(ValueError,'contract'):self.probe()

    def test_guard_successor_refused(self):
        self.info=(*self.info[:6],GUARD,self.info[-1])
        with self.assertRaisesRegex(ValueError,'contract'):self.probe()

    def test_noninteger_successor_refused(self):
        self.info=(*self.info[:6],(34<<26)|(9<<21)|(7<<16),self.info[-1])
        with self.assertRaisesRegex(ValueError,'contract'):self.probe()

    def test_stale_root_refused(self):
        self.old[T]=(LBZ,INTEGER)
        with self.assertRaisesRegex(ValueError,'history'):self.probe()

    def test_truncated_caller_refused(self):
        self.old[P]=(GUARD,GUARD,BL)
        with self.assertRaisesRegex(ValueError,'history'):self.probe()

    def test_return_guard_refused(self):
        self.old[P]=(GUARD,GUARD,BL,INTEGER)
        self.new[P]=self.old[P]
        with self.assertRaisesRegex(ValueError,'history'):self.probe()

    def test_extra_root_refused(self):
        self.new[T-0x100]=(GUARD,)
        with self.assertRaisesRegex(ValueError,'history'):self.probe()

    def test_caller_word_refused(self):
        self.caller=(P,16,C,BL^1,T,LBZ,C+4)
        with self.assertRaisesRegex(ValueError,'call'):self.probe()

    def test_caller_return_refused(self):
        self.caller=(P,16,C,BL,T,LBZ,C+8)
        with self.assertRaisesRegex(ValueError,'history'):self.probe()

    def test_successor_divergence_refused(self):
        self.new[T]=(LBZ,INTEGER^1,GUARD)
        with self.assertRaisesRegex(ValueError,'history'):self.probe()

    def test_sibling_mutation_refused(self):
        self.new[P]=(INTEGER,GUARD,BL,GUARD)
        with self.assertRaisesRegex(ValueError,'overlap'):self.probe()

if __name__=='__main__':
    unittest.main(verbosity=2)
