#!/usr/bin/env python3
import unittest
from prepare_formatter_caller_branch_contract import extend
from guarded_continuation import GUARD
P=0x80010000;SP=-864;LOAD=0x88610013;CALL=0x48000001
def d(op,r,a,n):return (op<<26)|(r<<21)|(a<<16)|(n&0xffff)
def bc(bo,bi,disp):return (16<<26)|(bo<<21)|(bi<<16)|(disp&0xfffc)
class BranchContract(unittest.TestCase):
    def setUp(self):
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        self.gp=list(self.initial);self.gp[1]=('stack',SP-48)
        self.add=d(14,4,3,1);self.cmp=d(11,0,4,0)
        self.w=bc(12,0,16);self.pc=P+16;self.second=bc(12,1,16)
        self.words=[CALL,LOAD,self.add,self.cmp,self.w,self.second]+[0x60000000]*8
        self.byte=({},(P,P+4,LOAD,CALL,19,9,P+8,self.add))
        self.rows=((P+8,self.add,((3,9),)),(P+12,self.cmp,((4,10),)))
        self.blocks={P:tuple(self.words[:5])+(GUARD,)}
    def probe(self):return extend(self.byte,(self.blocks,self.rows,self.pc,self.w),self.gp,self.initial,self.words,0)
    def test_fallthrough(self):
        (blocks,info),second=self.probe()
        self.assertEqual(info,(P,4*len(self.words),self.pc,self.w,False,P+20,self.second,P+32))
        self.assertEqual(blocks[P][5],self.second);self.assertEqual(blocks[P][8],GUARD)
        self.assertEqual(second[:3],('conditional',False,True))
    def test_taken(self):
        self.w=bc(12,1,16);self.words[4]=self.w;self.blocks[P]=tuple(self.words[:5])+(GUARD,)
        (blocks,info),_=self.probe()
        self.assertEqual(info[4:6],(True,P+32));self.assertEqual(blocks[P][5],GUARD)
    def test_unknown(self):
        self.w=bc(12,3,16);self.words[4]=self.w;self.blocks[P]=tuple(self.words[:5])+(GUARD,)
        with self.assertRaisesRegex(ValueError,'edge'):self.probe()
    def test_counter(self):
        self.w=bc(8,0,16);self.words[4]=self.w;self.blocks[P]=tuple(self.words[:5])+(GUARD,)
        with self.assertRaisesRegex(ValueError,'edge'):self.probe()
    def test_history(self):
        self.words[0]^=1
        with self.assertRaisesRegex(ValueError,'history'):self.probe()
    def test_existing_edge(self):
        self.blocks[P]=tuple(self.words[:6])+(GUARD,)
        with self.assertRaisesRegex(ValueError,'chosen'):self.probe()
    def test_historical_successor_preserved(self):
        self.blocks[P]=tuple(self.words[:5])+(GUARD,self.words[6],GUARD,GUARD,self.words[9])
        (blocks,_),_=self.probe()
        self.assertEqual(blocks[P][6],self.words[6])
        self.assertEqual(blocks[P][9],self.words[9])
        self.assertEqual(blocks[P][8],GUARD)
    def test_alternate_occupied(self):
        self.blocks[P]=tuple(self.words[:5])+(GUARD,GUARD,GUARD,self.words[8])
        with self.assertRaisesRegex(ValueError,'alternate'):self.probe()
    def test_changed_proof(self):
        self.rows=(self.rows[0],(P+12,self.cmp,((4,9),)))
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
