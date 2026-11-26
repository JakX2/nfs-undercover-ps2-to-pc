#!/usr/bin/env python3
"""Original-free regressions for the profiling preflight."""
import struct
import unittest
from make_private_elf_symbol_map import HEADER, SECTION, SYMBOL
from prepare_ipc_profile_geometry import OBJECTS, layout, inspect_leaf

A=0x80010000
P=0x80020000

def fixture(*,missing=-1,duplicate=False,overlap=False,wrong_size=False,wrong_type=False):
    elf=bytearray(2048)
    ident=b'\x7fELF\x01\x02\x01'+bytes(9)
    HEADER.pack_into(elf,0,ident,2,20,1,0,0,64,0,HEADER.size,0,0,SECTION.size,4,0)
    strings=b'\0';entries=[]
    for i,label in enumerate(OBJECTS):
        offset=len(strings);strings+=label+b'\0'
        if i==missing:continue
        addr=A+(0 if overlap and i==1 else 4*i if i<2 else 128*(i-1))
        length=4 if i<2 else 128
        if wrong_size and i==3:length=124
        entries.append((offset,addr,length,2 if wrong_type and i==2 else 1,0,3))
        if duplicate and i==0:entries.append((offset,A+16,4,1,0,3))
    sections=[(0,)*10,(0,3,0,0,512,len(strings),0,0,1,0),
              (0,2,0,0,768,len(entries)*SYMBOL.size,1,0,4,SYMBOL.size),
              (0,8,3,A,0,1024,0,0,4,0)]
    for i,row in enumerate(sections):SECTION.pack_into(elf,64+i*SECTION.size,*row)
    elf[512:512+len(strings)]=strings
    for i,row in enumerate(entries):SYMBOL.pack_into(elf,768+i*SYMBOL.size,*row)
    dol=bytearray(1024)
    struct.pack_into('>II',dol,0xd8,A,1024)
    return dol,elf

class TestLayout(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(layout(*fixture()),((A,4),(A+4,4),(A+128,128),(A+256,128)))
    def test_missing_and_conflicting(self):
        for k in (dict(missing=i) for i in range(4)):
            with self.subTest(k=k),self.assertRaisesRegex(ValueError,'object identity'):layout(*fixture(**k))
        for k,why in ((dict(duplicate=True),'identity'),(dict(overlap=True),'overlap'),
                      (dict(wrong_size=True),'array shape'),(dict(wrong_type=True),'type')):
            with self.subTest(k=k),self.assertRaisesRegex(ValueError,why):layout(*fixture(**k))
    def test_dol_geometry(self):
        for off,val,why in ((0xdc,64,'DOL span'),(0x48,A,'text overlap'),(0x64,A+2,'DOL span')):
            with self.subTest(off=off):
                d,e=fixture()
                if off==0x48:struct.pack_into('>I',d,0x90,32)
                if off==0x64:
                    struct.pack_into('>I',d,0xac,4)
                    struct.pack_into('>I',d,0x1c,256)
                struct.pack_into('>I',d,off,val)
                with self.assertRaisesRegex(ValueError,why):layout(d,e)
    def test_elf_header(self):
        d,e=fixture();e[5]=1
        with self.assertRaisesRegex(ValueError,'ELF header'):layout(d,e)

class TestLeaf(unittest.TestCase):
    # Synthetic PPC instructions; not extracted from any game.
    ST=36<<26
    STX=(31<<26)|(151<<1)
    BLR=0x4e800020
    BC=(16<<26)|(12<<21)|8
    BDNZ=(16<<26)|(16<<21)|0xfffc
    def test_paths(self):
        self.assertEqual(inspect_leaf(P,(self.ST,self.ST,self.BC,self.STX,self.ST,self.BLR)),(6,1,1,0))
        self.assertEqual(inspect_leaf(P,(self.ST,self.ST,self.ST,self.STX,self.BDNZ,self.BLR)),(6,1,1,1))
    def test_refusals(self):
        for word,why in ((0x44000002,'control'),(0x4e800420,'control'),(0x48000001,'edge'),
                         (0x48001000,'edge'),(37<<26,'store form')):
            with self.subTest(word=word),self.assertRaisesRegex(ValueError,why):
                inspect_leaf(P,(word,self.ST,self.ST,self.ST,self.ST,self.BLR))
        with self.assertRaisesRegex(ValueError,'store count'):inspect_leaf(P,(self.ST,self.BLR))
        with self.assertRaisesRegex(ValueError,'edge'):inspect_leaf(P,(self.ST,)*4)
if __name__=='__main__':unittest.main(verbosity=2)
