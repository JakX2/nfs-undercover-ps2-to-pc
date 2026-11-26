#!/usr/bin/env python3
import unittest
from prepare_formatter_nested_contract import contract,byte_cells
from guarded_continuation import GUARD
R=0x80010000;A=0x80020000;L=0x80030000;N=0x60000000
class Tests(unittest.TestCase):
    def setUp(self):
        self.initial=[('reg',i) for i in range(32)];self.initial[1]=('stack',-864)
        self.gp=self.initial.copy();self.gp[1]=('stack',-912)
        self.parent={-800:('byte',0)}
        self.mem=dict(self.parent)
        for a,v in ((-912,self.initial[1]),(-860,('const',L))):
            self.mem.update({a+i:b for i,b in enumerate(byte_cells(v,4))})
        self.path=tuple(R+4*i for i in range(36))
        self.ws=(N,)*35+(0x80630000,)
        self.sites=tuple((R+4*i,'stack_write',1,-910+i) for i in range(12))+((R+48,'const_read',4,A),)
    def run_contract(self):
        return contract((R,self.initial,self.parent,L,((A,b'abcd'),)),(A,4,self.path,48,self.sites,self.gp,self.mem,{},None,('const',L),frozenset()),self.ws,{R:(N,GUARD)},lambda a,n:None)
    def test_contract(self):
        blocks,fields,rows,access,slots,known=self.run_contract()
        self.assertEqual((len(rows),len(access),slots), (35,13,((4,32),)))
        self.assertEqual(blocks[R][-2:],(self.ws[-1],GUARD))
        self.assertEqual(known,((R+48,A,b'abcd'),))
    def test_linkage(self):
        self.mem[-860]=('byte',0)
        with self.assertRaisesRegex(ValueError,'linkage'):self.run_contract()
    def test_parent(self):
        self.mem[-800]=('byte',1)
        with self.assertRaisesRegex(ValueError,'parent'):self.run_contract()
    def test_nonvolatile(self):
        self.gp[14]=('const',1)
        with self.assertRaisesRegex(ValueError,'nonvolatile'):self.run_contract()
if __name__=='__main__':unittest.main(verbosity=2)
