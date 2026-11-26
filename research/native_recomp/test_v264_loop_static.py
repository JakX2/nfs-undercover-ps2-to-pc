#!/usr/bin/env python3
"""V264 synthetic PowerPC structure tests: no original executable needed."""
import unittest
import struct
from make_private_elf_symbol_map import HEADER,SECTION
from pathlib import Path
from audit_v264_osinit_retry_elf import (
    CALLSITE, HELPER, DISABLE, RESTORE, GETTIME,
    classify, private_audit, format_result,read_words,_text_sections,
)

def bl(pc:int,dest:int,lk:int=1)->int:
    d=dest-pc
    assert d%4==0 and -(1<<25)<=d<1<<25
    return 18<<26 | (d&0x03fffffc) | lk

def sample():
    start=CALLSITE-24
    body=[0x60000000]*96
    idx=6
    body[idx]=bl(CALLSITE,HELPER)
    body[idx+1]=11<<26
    body[idx+2]=(34<<26)|(13<<16)|((-3176)&0xffff)
    body[idx+3]=16<<26|((-12)&0xfffc)
    helper=[0x60000000]*80
    helper[6]=bl(HELPER+24,DISABLE)
    helper[62]=bl(HELPER+248,RESTORE)
    helper[10]=bl(HELPER+40,GETTIME)
    helper[16]=31<<26|371<<1
    return start,body,helper

class Tests(unittest.TestCase):
    def test_branches_and_os_helpers(self):
        x=classify(*sample())
        for k in ("direct","link","cond","backward","back_to_call","back_cond",
                  "compare","sda_loads","sc_sda","sc_byte",
                  "disable","restore","gettime","mftb"):
            self.assertEqual(x[k],1,k)
        self.assertEqual(x["back_span"],12)
        self.assertEqual(x["window"],65 if False else 64)
        self.assertIn("V264_LOOP_STRUCT owner=1 direct=1 link=1",format_result(x))
        self.assertNotIn("0x60000000",format_result(x))

    def test_fail_closed_and_indirect(self):
        start,caller,helper=sample()
        with self.assertRaisesRegex(ValueError,"geometry"):
            classify(CALLSITE+4,caller,helper)
        with self.assertRaisesRegex(ValueError,"geometry"):
            classify(start,caller[:8],helper)
        with self.assertRaisesRegex(ValueError,"digest"):
            private_audit(b"not a Wii original ELF")
        bad=caller.copy()
        bad[6]=bl(CALLSITE,HELPER+4)
        self.assertEqual(classify(start,bad,helper)["direct"],0)

    def test_cached_text_reads(self):
        base=0x80010000
        ident=b'\x7fELF\x01\x02\x01'+bytes(9)
        def elf(rows):
            off=HEADER.size+len(rows)*SECTION.size
            h=HEADER.pack(ident,2,20,1,0,0,HEADER.size,0,HEADER.size,0,0,SECTION.size,len(rows),0)
            sections=b''.join(SECTION.pack(0,kind,flags,addr,off,8,0,0,4,0) for kind,flags,addr in rows)
            return h+sections+struct.pack('>II',0x60000000,0x4e800020)
        raw=elf(((1,4,base),(8,4,base),(1,2,base)))
        _text_sections.cache_clear()
        first=read_words(raw,base,2);first[0]=0
        self.assertEqual(read_words(raw,base,2),[0x60000000,0x4e800020])
        self.assertEqual(read_words(raw,base+4,1),[0x4e800020])
        self.assertEqual((_text_sections.cache_info().misses,_text_sections.cache_info().hits),(1,2))
        for at,n in ((base+8,1),(base,3),(base+1,1),(base,0)):
            with self.assertRaises(ValueError):read_words(raw,at,n)
        with self.assertRaisesRegex(ValueError,'section'):
            read_words(elf(((1,4,base),(1,4,base))),base,1)
        mutable=bytearray(raw)
        self.assertEqual(read_words(mutable,base,1),[0x60000000])
        struct.pack_into('>I',mutable,HEADER.size+12,base+8)
        with self.assertRaisesRegex(ValueError,'section'):read_words(mutable,base,1)
        _text_sections.cache_clear()
    def test_private_ci_boundary(self):
        wf=(Path(__file__).resolve().parents[2]/
            ".github/workflows/wii-v264-loop-static.yml").read_text(encoding="utf-8")
        self.assertIn("V264_ORIGINAL_ELF verified=1",wf)
        self.assertIn("WII_ORIGINAL_ELF_ID",wf)
        self.assertIn("stage_owner_wii_gdown.py",wf)
        self.assertNotIn("upload-artifact",wf)
        self.assertEqual(wf.count("      - name: Remove private owner inputs"),1)

if __name__=="__main__":
    unittest.main()
