#!/usr/bin/env python3
import unittest
from prepare_formatter_partial_native_contract import extend,read_address,read_value,extra_census
from guarded_continuation import GUARD
from prepare_formatter_nested_contract import byte_cells
R=0x80010000;L=0x80020000;SP=-864;F=48;AT=SP-40
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
class Contract(unittest.TestCase):
    def setUp(self):
        self.words=[0x60000000]*383
        self.rows=tuple((R+4*i,self.words[i]) for i in range(84))
        self.start=R+336;self.words[84]=d(32,3,1,8)
        self.fields=(R,L,self.start,self.words[84],48,-40,4)
        self.slots=((4,32),(-4,14),(-8,15),(-12,16))
        self.access=tuple((R+4*i,4,-48,True,True) for i in range(13))+tuple((R+4*(13+i),4,0x80030000+4*i,False,False) for i in range(5))+tuple((R+4*(18+i),4,-8,True,False) for i in range(3))
        self.known=tuple((pc,a,b'abcd') for pc,n,a,s,w in self.access if not s)
        self.old=({R:tuple(self.words[:85])+(GUARD,)},self.fields,self.rows,self.access,self.slots,self.known)
        self.initial=[('reg',r) for r in range(32)];self.initial[1]=('stack',SP)
        gp=list(self.initial);gp[1]=('stack',SP-F);gp[4]=('const',9)
        mem={AT:('byte',0x12),AT+1:('byte',0x34)}
        for off,r in self.slots:
            v=('const',L) if r==32 else self.initial[r]
            mem.update({SP+off+j:c for j,c in enumerate(byte_cells(v,4))})
        self.entry=(R,tuple(self.initial),{},L,())
        self.record=(AT,4,tuple(pc for pc,_ in self.rows)+(self.start,),F,(),tuple(gp),dict(mem),{},None,('const',L),frozenset())
        self.trace=[];self.admitted=[]
        for i in range(12):
            pc=self.start+4*i
            if i in (3,4,6,9):
                off={3:16,4:20,6:24,9:28}[i]
                rs=3 if i==4 else 4
                self.words[84+i]=d(36,rs,1,F+off)
                self.admitted.append((pc,SP+off,4,'partial' if rs==3 else 'const'))
            self.trace.append((pc,self.words[84+i],tuple(gp),dict(mem)))
            if i==0:gp[3]=('partial',(('byte',0x12),('byte',0x34),('uninitialized',AT+2),('uninitialized',AT+3)))
            elif i in (3,4,6,9):
                _,a,n,k=self.admitted[-1]
                data=gp[3][1] if k=='partial' else byte_cells(gp[4],4)
                mem.update({a+j:c for j,c in enumerate(data)})
    def probe(self):return extend(self.old,self.trace,self.admitted,self.entry,self.record,self.words)
    def test_exact(self):
        c=self.probe();self.assertEqual((len(c[2]),len(c[3]),c[1][2]),(95,26,self.start+44))
        self.assertEqual(c[3][-4:],tuple((pc,n,a-SP,True,True) for pc,a,n,k in self.admitted))
    def test_wrong_store(self):
        self.admitted[0]=(self.admitted[0][0],SP+4,4,'const')
        with self.assertRaisesRegex(ValueError,'caller sites|caller geometry'):self.probe()
    def test_changed_parent(self):
        self.entry=self.entry[:2]+({SP+16:('byte',8)},)+self.entry[3:]
        with self.assertRaisesRegex(ValueError,'caller sites|caller geometry'):self.probe()
    def test_unknown_copy(self):
        p,w,g,m=self.trace[5];m=dict(m);m[SP+22]=('byte',0);self.trace[5]=(p,w,g,m)
        with self.assertRaisesRegex(ValueError,'caller effects'):self.probe()
    def test_boundary(self):
        p,w,g,m=self.trace[-1];self.trace[-1]=(p,d(32,3,1),g,m);self.words[95]=d(32,3,1)
        with self.assertRaisesRegex(ValueError,'boundary'):self.probe()
    def test_extra_access(self):
        p,w,g,m=self.trace[2];self.trace[2]=(p,d(32,3,1),g,m);self.words[86]=d(32,3,1)
        with self.assertRaisesRegex(ValueError,'extra access|read provenance'):self.probe()
    def test_known_local_reload(self):
        p,w,g,m=self.trace[2];self.words[86]=d(40,4,1,8)
        self.trace[2]=(p,self.words[86],g,m)
        p,w,g,m=self.trace[3];g=list(g);g[4]=('const',0x1234);self.trace[3]=(p,w,tuple(g),m)
        # Later store effect is still 9 in the fixture; it must fail rather than accept that inconsistent write.
        with self.assertRaisesRegex(ValueError,'caller effects'):self.probe()
        self.assertEqual(read_address(self.words[86],g),('stack',AT,2))
        self.assertEqual(read_value((('byte',0x12),('byte',0x34)),self.words[86]),('const',0x1234))
        self.assertEqual(extra_census(self.trace,self.admitted,self.entry),{('load','child',2,2,0):1})
    def test_signed_and_opaque_read(self):
        self.assertEqual(read_value((('byte',0x80),('byte',1)),d(42,4,1)),('const',0xffff8001))
        self.assertEqual(read_value((('uninitialized',AT),('byte',1)),d(40,4,1)),('partial',(('byte',0),('byte',0),('uninitialized',AT),('byte',1))))
        with self.assertRaisesRegex(ValueError,'provenance'):read_value((None,('byte',1)),d(40,4,1))
if __name__=='__main__':unittest.main(verbosity=2)
