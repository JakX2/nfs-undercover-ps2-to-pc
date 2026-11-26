#!/usr/bin/env python3
"""Synthetic ELF/DOL fixtures for the private ring identity parser."""
import struct,unittest
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL
from prepare_v1414_ipc_ring import ring_object,ring_sites
BASE=0x80010000

def fixture(*,name=b'__responses',length=80,flags=3,kind=8,typ=1,addr=BASE,duplicate=False,link=1):
    raw=bytearray(0x400)
    ident=b'\x7fELF\x01\x02\x01'+b'\0'*9
    HEADER.pack_into(raw,0,ident,2,20,1,0,0,0x40,0,HEADER.size,0,0,SECTION.size,4,0)
    strings=b'\0'+name+b'\0'
    raw[0x180:0x180+len(strings)]=strings
    entries=[(0,0,0,0,0,0),(1,addr,length,typ,0,3)]
    if duplicate:entries.append((1,addr+0x100,length,typ,0,3))
    sections=[(0,)*10,(0,3,0,0,0x180,len(strings),0,0,1,0),
              (0,2,0,0,0x200,len(entries)*SYMBOL.size,link,1,4,SYMBOL.size),
              (0,kind,flags,BASE,0x300,0x1000,0,0,4,0)]
    for i,sec in enumerate(sections):SECTION.pack_into(raw,0x40+i*SECTION.size,*sec)
    for i,sym in enumerate(entries):SYMBOL.pack_into(raw,0x200+i*SYMBOL.size,*sym)
    dol=bytearray(0x400)
    struct.pack_into('>II',dol,0xd8,BASE,0x1000)
    return dol,raw

class Geometry(unittest.TestCase):
    def test_exact(self):
        for slots in (2,16,48,64):
            d,e=fixture(length=16+4*slots)
            self.assertEqual(ring_object(d,e),(BASE,16+4*slots,slots))
    def test_identity_refusals(self):
        for kw in ({'name':b'__responses_extra'},{'name':b'other'},{'duplicate':True},
                   {'typ':2},{'flags':2},{'flags':7},{'kind':3},{'addr':BASE+1},
                   {'addr':BASE-4},{'length':20},{'length':81},{'length':276},{'link':0}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):
                ring_object(*fixture(**kw))
    def test_dol_bounds(self):
        d,e=fixture();struct.pack_into('>I',d,0xdc,32)
        with self.assertRaises(ValueError):ring_object(d,e)
        d,e=fixture();struct.pack_into('>I',d,0x48,BASE);struct.pack_into('>I',d,0x90,80)
        with self.assertRaises(ValueError):ring_object(d,e)
    def test_initialized_data_geometry(self):
        def data_fixture():
            d,e=fixture(kind=1)
            for off,value in ((0x1c,256),(0x64,BASE),(0xac,256)):
                struct.pack_into('>I',d,off,value)
            return d,e
        d,e=data_fixture()
        self.assertEqual(ring_object(d,e),(BASE,80,16))
        for changes in (((0x1c,0),),((0x1c,900),),((0xac,32),),
                        ((0x20,256),(0x68,BASE),(0xb0,256)),
                        ((0x64,BASE+64),(0xac,64))):
            with self.subTest(changes=changes):
                d,e=data_fixture()
                for off,value in changes:struct.pack_into('>I',d,off,value)
                with self.assertRaisesRegex(ValueError,'ring DOL range'):ring_object(d,e)
    def test_elf_header_geometry(self):
        for off,fmt,value in ((20,'I',2),(32,'I',0),(40,'H',0),(46,'H',0),(48,'H',0)):
            with self.subTest(off=off):
                d,e=fixture()
                struct.pack_into('>'+fmt,e,off,value)
                with self.assertRaisesRegex(ValueError,'ring ELF sections'):ring_object(d,e)
    def test_bad_elf(self):
        d,e=fixture();e[5]=1
        with self.assertRaises(ValueError):ring_object(d,e)
        d,e=fixture()
        with self.assertRaises(ValueError):ring_object(d,e[:100])
    def test_sites(self):
        owner=0x80020000;first=owner+16;stop=owner+40
        w=0x90650000
        words={first:(owner,w),first+4:(owner,w),first+12:(owner,w),stop:(owner,0x60000000)}
        self.assertEqual(ring_sites(words,owner,first,stop),(first,first+4,first+12))
        for bad in ({k:v for k,v in words.items() if k!=first},
                    {**words,first+8:(owner,w)}, {**words,first:(owner,0x90610000)},
                    {**words,first+12:(owner+4,w)}):
            with self.assertRaises(ValueError):ring_sites(bad,owner,first,stop)
if __name__=='__main__':unittest.main()
