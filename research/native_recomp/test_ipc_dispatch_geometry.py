#!/usr/bin/env python3
"""Original-free tests for dispatch credit and corridor geometry."""
import struct
import unittest
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL
from prepare_ipc_dispatch_geometry import credit_object,corridor

A=0x80010000
P=0x80020000
W=0x80030000
R=W+4
N=0x60000000
ST=36<<26
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def bc(pc,dst):return (16<<26)|(12<<21)|((dst-pc)&0xfffc)
CALLS={P+8:W,P+24:R,P+32:W}
WORDS=(bc(P,P+40),N,bl(P+8,W),ST,ST,ST,bl(P+24,R),N,bl(P+32,W),N,0x4e800020)
def fixture(*,name=b'__mailboxAck',length=4,flags=3,typ=1,duplicate=False):
    elf=bytearray(1024)
    HEADER.pack_into(elf,0,b'\x7fELF\x01\x02\x01'+bytes(9),2,20,1,0,0,64,0,HEADER.size,0,0,SECTION.size,4,0)
    strings=b'\0'+name+b'\0'
    entries=[(1,A,length,typ,0,3)]
    if duplicate:entries.append((1,A+4,length,typ,0,3))
    sections=[(0,)*10,(0,3,0,0,256,len(strings),0,0,1,0),
              (0,2,0,0,384,len(entries)*SYMBOL.size,1,0,4,SYMBOL.size),(0,8,flags,A,0,64,0,0,4,0)]
    for i,row in enumerate(sections):SECTION.pack_into(elf,64+i*SECTION.size,*row)
    elf[256:256+len(strings)]=strings
    for i,row in enumerate(entries):SYMBOL.pack_into(elf,384+i*SYMBOL.size,*row)
    dol=bytearray(512);struct.pack_into('>II',dol,0xd8,A,64)
    return dol,elf
class Credit(unittest.TestCase):
    def test_exact(self):self.assertEqual(credit_object(*fixture()),(A,4))
    def test_bad(self):
        for kw in (dict(name=b'__mailboxAck_other'),dict(length=8),dict(flags=7),dict(typ=2),dict(duplicate=True)):
            with self.subTest(kw=kw),self.assertRaises(ValueError):credit_object(*fixture(**kw))
        d,e=fixture();struct.pack_into('>I',d,0xdc,2)
        with self.assertRaisesRegex(ValueError,'DOL span'):credit_object(d,e)
class Corridor(unittest.TestCase):
    def run_lane(self,words=WORDS,calls=CALLS):return corridor(P,words,P,P+8,P+24,P+32,calls)
    def test_valid(self):self.assertEqual(self.run_lane(),(9,1,0,3,0))
    def test_refusals(self):
        for i,w,why in ((0,bc(P,P+24),'dominance'),(3,N,'store count'),(4,37<<26,'store form'),
                        (2,bl(P+8,R),'call identity'),(1,0x44000002,'control')):
            with self.subTest(i=i),self.assertRaisesRegex(ValueError,why):
                words=list(WORDS);words[i]=w;self.run_lane(tuple(words))
        with self.assertRaisesRegex(ValueError,'call roles'):self.run_lane(calls={**CALLS,P+24:W})
if __name__=='__main__':unittest.main(verbosity=2)
