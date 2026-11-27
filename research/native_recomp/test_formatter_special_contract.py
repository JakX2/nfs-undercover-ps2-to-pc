#!/usr/bin/env python3
import unittest
from prepare_formatter_special_contract import extend
from guarded_continuation import GUARD
R=0x80010000;L=0x80020000
def mtspr(rs,spr):return (31<<26)|(rs<<21)|((spr&31)<<16)|((spr>>5)<<11)|(467<<1)
class Special(unittest.TestCase):
    def setUp(self):
        self.words=[0x60000000]*383;self.pc=R+380;self.w=mtspr(3,8)
        self.words[95]=self.w;self.words[96]=0x4e800020
        self.rows=tuple((R+4*i,self.words[i]) for i in range(95))
        self.access=tuple((R+4*i,4,-48,True,i<17) for i in range(32))
        self.slots=((4,32),(-4,14),(-8,15),(-12,16));self.known=tuple(range(5))
        self.gp=[('reg',r) for r in range(32)];self.gp[3]=('const',L)
        self.blocks={R:tuple(self.words[:96])+(GUARD,)}
    def probe(self):
        return extend((self.blocks,(R,L,self.pc,self.w,48,0,0),self.rows,self.access,self.slots,self.known),
                      (self.pc,self.w,tuple(self.gp),{}),self.words)
    def test_lr(self):
        c,info=self.probe();self.assertEqual(info,('link',1,'return'))
        self.assertEqual((len(c[2]),len(c[3]),c[1][2],c[1][3]),(96,32,self.pc+4,0x4e800020))
        self.assertEqual(c[0][R][-1],GUARD);self.assertEqual(c[3],self.access)
    def test_ctr(self):
        self.w=mtspr(3,9);self.words[95]=self.w;self.blocks[R]=tuple(self.words[:96])+(GUARD,)
        self.assertEqual(self.probe()[1],('count',0,'return'))
    def test_unproven(self):
        for v in (('partial',()),('reg',3),('stack',-4)):
            self.gp[3]=v
            with self.assertRaisesRegex(ValueError,'source'):self.probe()
    def test_unsupported(self):
        for w in (mtspr(3,1),mtspr(3,8)|1,0x60000000):
            self.w=w;self.words[95]=w;self.blocks[R]=tuple(self.words[:96])+(GUARD,)
            with self.assertRaisesRegex(ValueError,'source'):self.probe()
    def test_original_mismatch(self):
        self.words[95]^=1
        with self.assertRaisesRegex(ValueError,'words'):self.probe()
    def test_existing_boundary(self):
        self.blocks[R]=tuple(self.words[:97])+(GUARD,)
        with self.assertRaisesRegex(ValueError,'old words'):self.probe()
    def test_guard(self):
        self.words[96]=GUARD
        with self.assertRaisesRegex(ValueError,'words'):self.probe()
    def test_changed_history(self):
        self.words[10]^=1
        with self.assertRaisesRegex(ValueError,'overlap'):self.probe()
    def test_invalid_access_count(self):
        self.access=self.access[:-1]
        with self.assertRaisesRegex(ValueError,'predecessor'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
