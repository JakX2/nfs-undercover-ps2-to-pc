import unittest
from prepare_v1388_ioctl_dataflow import A,C,P,R,S,apply,paths,verify

def st(rs,ra,off):return 36<<26|rs<<21|ra<<16|(off&0xffff)
def mr(rd,rs):return 31<<26|rs<<21|rd<<16|rs<<11|444<<1
def li(rd,n):return 14<<26|rd<<21|(n&0xffff)
def phys(rd,rs):return 21<<26|rs<<21|rd<<16|2<<6|31<<1
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Tests(unittest.TestCase):
    def test_wire_provenance(self):
        r=0x80004000;t=r+0x1000
        w=[];edges=[]
        def call(n):
            pc=r+4*len(w);edges.append((pc,t+4*n));w.append(bl(pc,t+4*n))
        call(0)
        for reg in range(3,11):w.append(mr(reg+20,reg))
        call(1)
        w.append(mr(22,3));w.append(li(0,6));w.append(st(0,22,0))
        for reg,off in ((23,8),(24,12),(26,20),(28,28),(29,32),(30,36)):w.append(st(reg,22,off))
        w.extend((phys(0,25),st(0,22,16),phys(0,27),st(0,22,24)))
        call(2);call(3);w.append(mr(3,22));call(4);call(5);w.append(0x4e800020)
        result=paths(r,w,edges)
        self.assertEqual(verify(result)[0],(32,36))
        for off in (0,8,12,16,20,24,28,32,36):
            req,wire,flush=result[0][0]
            bad={**wire,off:None}
            with self.assertRaises(ValueError):verify(([(req,bad,flush)],result[1],result[2]))
    def test_unknown_destroys_or_rejects(self):
        regs=[None]*32;regs[3]=A(3);regs[22]=R();regs[1]=S()
        stack={};wire={}
        apply(mr(23,3),regs,stack,wire);self.assertEqual(regs[23],A(3))
        apply(phys(23,3),regs,stack,wire);self.assertEqual(regs[23],P(3))
        apply(st(23,22,8),regs,stack,wire);self.assertEqual(wire[8],P(3))
        with self.assertRaises(ValueError):apply(st(23,21,0),regs,stack,wire)
        with self.assertRaises(ValueError):apply(st(23,22,64),regs,stack,wire)
        with self.assertRaises(ValueError):apply(0xffffffff,regs,stack,wire)
        apply(li(23,6),regs,stack,wire);self.assertEqual(regs[23],C(6))
if __name__=='__main__':unittest.main()
