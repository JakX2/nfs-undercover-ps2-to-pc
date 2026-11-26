#!/usr/bin/env python3
import struct
import unittest
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL
from prepare_stm_event_return_geometry import stores,object_at,_object_at_cached
S=0x80010000
A=0x80020000
B={13:A+16}
def op(n,rs,ra,imm):return n<<26|rs<<21|ra<<16|(imm&0xffff)
def fixture():
    elf=bytearray(1024)
    HEADER.pack_into(elf,0,b'\x7fELF\x01\x02\x01'+bytes(9),2,20,1,0,0,64,0,HEADER.size,0,0,SECTION.size,4,0)
    strings=b'\0synthetic\0'
    sections=[(0,)*10,(0,3,0,0,256,len(strings),0,0,1,0),
              (0,2,0,0,384,SYMBOL.size,1,0,4,SYMBOL.size),(0,8,3,A,0,64,0,0,4,0)]
    for i,row in enumerate(sections):SECTION.pack_into(elf,64+i*SECTION.size,*row)
    elf[256:256+len(strings)]=strings
    SYMBOL.pack_into(elf,384,1,A,16,1,0,3)
    dol=bytearray(512);struct.pack_into('>II',dol,0xd8,A,64)
    return dol,elf
class Geometry(unittest.TestCase):
    def test_stores(self):
        words=(op(36,3,13,-16),op(38,4,13,-12),op(44,5,13,-10),0x60000000)
        self.assertEqual(stores(S,words,range(S,S+16,4),B),((S,A,4,3),(S+4,A+4,1,4),(S+8,A+6,2,5)))
    def test_alternate_sites_same_flag(self):
        words=(op(36,3,13,-16),op(36,4,13,-16))
        self.assertEqual(stores(S,words,[S,S+4],B),((S,A,4,3),(S+4,A,4,4)))
        with self.assertRaises(ValueError):stores(S,words,[S,S],B)
    def test_refusals(self):
        for w in (op(36,3,1,0),op(37,3,13,0),op(36,3,13,-1),op(31,3,13,151<<1)):
            with self.subTest(w=w),self.assertRaises(ValueError):stores(S,(w,),[S],B)
    def test_immutable_cache(self):
        _object_at_cached.cache_clear()
        d,e=fixture();raw=bytes(d);elf=bytes(e)
        self.assertEqual(object_at(raw,elf,A+4,4),(A,16))
        self.assertEqual(object_at(raw,elf,A+4,4),(A,16))
        self.assertEqual(_object_at_cached.cache_info().hits,1)
        struct.pack_into('>I',d,0xdc,8)
        with self.assertRaises(ValueError):object_at(bytes(d),elf,A+4,4)
        self.assertEqual(object_at(raw,elf,A+4,4),(A,16))
        _object_at_cached.cache_clear()

    def test_object(self):
        d,e=fixture()
        self.assertEqual(object_at(d,e,A+4,4),(A,16))
        with self.assertRaises(ValueError):object_at(d,e,A+16,4)
        struct.pack_into('>I',d,0xdc,8)
        with self.assertRaises(ValueError):object_at(d,e,A+4,4)
if __name__=='__main__':unittest.main(verbosity=2)
