#!/usr/bin/env python3
import unittest
from prepare_formatter_release_contract import extend
from prepare_formatter_nested_contract import byte_cells
from guarded_continuation import GUARD
R=0x80010000;L=0x80020000;SP=-864;F=48
class Release(unittest.TestCase):
    def setUp(self):
        self.words=[0x60000000]*383;self.pc=R+384;self.w=0x38210030;self.mtlr=(31<<26)|(3<<21)|(8<<16)|(467<<1)
        self.words[95:98]=[self.mtlr,self.w,0x4e800020]
        self.rows=tuple((R+4*i,self.words[i]) for i in range(96))
        self.access=tuple((R+4*i,4,-48,True,i<17) for i in range(32))
        self.slots=((4,32),(-4,14),(-8,15),(-12,16));self.known=tuple(range(5))
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        self.gp=list(self.initial);self.gp[1]=('stack',SP-F);self.gp[3]=('const',L)
        self.parent={SP+32:('byte',7)}
        self.mem=dict(self.parent)
        self.mem.update({SP-F+i:c for i,c in enumerate(byte_cells(self.initial[1],4))})
        for off,r in self.slots:
            v=('const',L) if r==32 else self.initial[r]
            self.mem.update({SP+off+i:c for i,c in enumerate(byte_cells(v,4))})
        self.blocks={R:tuple(self.words[:97])+(GUARD,)}
    def probe(self):
        return extend((self.blocks,(R,L,self.pc,self.w,F,0,0),self.rows,self.access,self.slots,self.known),
                      (self.pc-4,self.mtlr,self.gp,self.mem),(R,self.initial,self.parent,L,()),self.words)
    def test_exact(self):
        c=self.probe();self.assertEqual((len(c[2]),len(c[3]),c[1][2],c[1][3]),(97,32,self.pc+4,0x4e800020))
        self.assertEqual(c[0][R][-1],GUARD);self.assertEqual(c[3],self.access)
    def test_link(self):
        self.gp[3]=('const',L+4)
        with self.assertRaisesRegex(ValueError,'link'):self.probe()
    def test_nonvolatile(self):
        self.gp[14]=('const',0)
        with self.assertRaisesRegex(ValueError,'register identity'):self.probe()
    def test_sp(self):
        self.gp[1]=('stack',SP-F-4)
        with self.assertRaisesRegex(ValueError,'register identity'):self.probe()
    def test_backchain(self):
        self.mem[SP-F]=('byte',0)
        with self.assertRaisesRegex(ValueError,'backchain'):self.probe()
    def test_parent(self):
        self.mem[SP+32]=('byte',8)
        with self.assertRaisesRegex(ValueError,'parent identity'):self.probe()
    def test_linkage(self):
        self.mem[SP+4]=('byte',0)
        with self.assertRaisesRegex(ValueError,'saved register'):self.probe()
    def test_wrong_release(self):
        self.w=0x3821002c;self.words[96]=self.w
        with self.assertRaisesRegex(ValueError,'instruction shape'):self.probe()
    def test_wrong_return(self):
        self.words[97]=0x60000000
        with self.assertRaisesRegex(ValueError,'instruction shape'):self.probe()
    def test_old_word(self):
        self.blocks[R]=tuple(self.words[:98])+(GUARD,)
        with self.assertRaisesRegex(ValueError,'guarded words'):self.probe()
if __name__=='__main__':unittest.main(verbosity=2)
