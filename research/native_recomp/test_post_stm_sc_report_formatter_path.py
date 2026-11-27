#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_formatter_path import first_path,const
B=0x80001000;T=0x80002000;A=0x80003000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Path(unittest.TestCase):
    def test_path(self):
        ws=(0x9421ffe0,0x7c0802a6,0x90010024,0x93e1001c,0x88830000,0x2c040041,0x40820008,bl(B+28,T),0x4e800020)
        path,frame,accesses,saved,dst,*_=first_path(B,ws,{3:const(A)},{},((A,b'A\0'),))
        self.assertEqual((len(path),frame,len(accesses),saved,dst),(8,32,4,1,T))
        for bad in ((0x9421fffc,*ws[1:]),(*ws[:2],0x90010004,*ws[3:]),(*ws[:4],0x88830004,*ws[5:])):
            with self.assertRaises(ValueError):first_path(B,bad,{3:const(A)},{},((A,b'A\0'),))
    def test_partial_local_store(self):
        ws=(0x9421ffe0,0x7c0802a6,0x90010024,0x3860007f,0x98610008,
            0x88810008,0x2c04007f,0x40820008,bl(B+32,T),0x4e800020)
        path,frame,accesses,saved,dst,*_=first_path(B,ws,{},{},())
        self.assertEqual((len(path),frame,len(accesses),saved,dst),(9,32,4,0,T))
        for bad in ((*ws[:4],0x98610004,*ws[5:]),(*ws[:4],0x98610024,*ws[5:]),(*ws[:4],0x98610020,*ws[5:])):
            # The first slot is a legal local byte, so use a separate
            # unknown-read check rather than requiring it to be forbidden.
            with self.assertRaises(ValueError):first_path(B,bad,{},{},())
    def test_narrow_opaque_register(self):
        for store,load in ((0xb0a10008,0xa0c10008),(0x98a10008,0x88c10008),(0xb0a10008,0xa8c10008)):
            ws=(0x9421ffe0,0x7c0802a6,0x90010024,store,load,bl(B+20,T))
            with self.assertRaisesRegex(ValueError,'stack read provenance'):
                first_path(B,ws,{},{},())
        ws=(0x9421ffe0,0x7c0802a6,0x90010024,0x90a10008,0x80c10008,bl(B+20,T))
        result=first_path(B,ws,{},{},(),details=True)
        self.assertEqual(result[5][6],('reg',5))
def xload(xo,rt,ra,rb,rc=0):return (31<<26)|(rt<<21)|(ra<<16)|(rb<<11)|(xo<<1)|rc
class IndexedLoad(unittest.TestCase):
    def probe(self,word,args,readonly):
        ws=(0x9421ffe0,0x7c0802a6,0x90010024,word,bl(B+16,T))
        return first_path(B,ws,args,{},readonly,details=True)
    def test_integer_forms(self):
        for xo,n,v in ((23,4,0x81ff1234),(55,4,0x81ff1234),(87,1,0x81),(119,1,0x81),(279,2,0x81ff),(311,2,0x81ff),(343,2,0xffff81ff),(375,2,0xffff81ff)):
            with self.subTest(xo=xo):
                result=self.probe(xload(xo,4,3,5),{3:const(A-4),5:const(4)},((A,b'\x81\xff\x12\x34'),))
                self.assertEqual(result[5][4],const(v))
                self.assertEqual(result[2][-1],(B+12,'const_read',n,A))
                self.assertEqual(result[5][3],const(A if xo in (55,119,311,375) else A-4))
    def test_ra_zero(self):
        r=self.probe(xload(23,4,0,5),{0:const(99),5:const(A)},((A,b'abcd'),))
        self.assertEqual(r[5][4],const(0x61626364))
    def test_signed_index(self):
        r=self.probe(xload(23,4,3,5),{3:const(A+4),5:const(-4)},((A,b'abcd'),))
        self.assertEqual(r[5][4],const(0x61626364))
    def test_bad_form(self):
        for w in (xload(55,4,0,5),xload(55,4,4,5),xload(55,4,1,5),xload(23,1,3,5),xload(23,4,3,5,1)):
            with self.assertRaisesRegex(ValueError,'indexed load form'):
                self.probe(w,{3:const(A),5:const(0)},((A,b'abcd'),))
    def test_alignment_and_unknown(self):
        for args in ({3:const(A),5:const(1)},{}):
            with self.assertRaisesRegex(ValueError,'indexed load provenance'):
                self.probe(xload(23,4,3,5),args,((A,b'abcdefgh'),))
        with self.assertRaisesRegex(ValueError,'data read provenance'):
            self.probe(xload(23,4,3,5),{3:const(A),5:const(0)},())
class LocalCtr(unittest.TestCase):
    def setUp(self):
        self.site=B+20;self.dst=B+32
        self.ws=(0x9421ffe0,0x7c0802a6,0x90010024,0x80830000,0x7c8903a6,0x4e800420,0x60000000,0x60000000,0x38a00007,bl(B+36,T))
    def probe(self,edge,value=None):
        value=self.dst if value is None else value
        return first_path(B,self.ws,{3:const(A)},{},((A,value.to_bytes(4,'big')),),local_ctr_edge=edge,details=True)
    def test_exact(self):
        result=self.probe((self.site,self.dst))
        self.assertEqual(result[0],list(range(B,B+24,4))+[self.dst,self.dst+4])
        self.assertEqual(result[5][5],const(7));self.assertEqual(result[4],T)
    def test_default_refusal(self):
        with self.assertRaisesRegex(ValueError,'other boundary'):self.probe(None)
    def test_wrong_live_target(self):
        with self.assertRaisesRegex(ValueError,'CTR identity'):self.probe((self.site,self.dst),self.dst+4)
    def test_bad_geometry(self):
        for edge in ((self.site,self.dst+1),(self.site,T),(B+16,self.dst),(self.site,self.site),(self.site,B)):
            with self.assertRaisesRegex(ValueError,'CTR geometry'):self.probe(edge)
if __name__=='__main__':unittest.main(verbosity=2)
