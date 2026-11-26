#!/usr/bin/env python3
import unittest
from audit_formatter_nested_read import classify_section,direct_writers
from make_private_elf_symbol_map import HEADER,SECTION
from prepare_v419_full_start import EXPECTED_GPRS
A=0x80010000
def elf(flags,kind=1,base=A,size=4):
    ident=b'\x7fELF\x01\x02\x01'+bytes(9)
    return HEADER.pack(ident,2,20,1,0,0,52,0,52,0,0,40,1,0)+SECTION.pack(0,kind,flags,base,92,size,0,0,4,0)+bytes(4)
class Test(unittest.TestCase):
    def test_section(self):
        for flags,kind,name in ((2,1,'readonly'),(3,1,'writable'),(6,1,'executable'),(3,8,'bss')):
            self.assertEqual(classify_section(elf(flags,kind),A,4),name)
        self.assertEqual(classify_section(elf(3),A+2,4),'partial')
        self.assertEqual(classify_section(elf(3),A+4,4),'ambiguous')
    def test_direct_writers(self):
        a=EXPECTED_GPRS[13]
        stw=(36<<26)|(3<<21)|(13<<16)|4
        self.assertEqual(direct_writers((stw,),a+4,4),1)
        self.assertEqual(direct_writers((stw,),a+8,4),0)
        self.assertEqual(direct_writers((stw,),a+6,1),1)
if __name__=='__main__':unittest.main(verbosity=2)
