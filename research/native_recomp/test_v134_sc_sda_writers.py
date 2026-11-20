#!/usr/bin/env python3
"""V134 original-free PPC r13 SDA memory xref decoding tests."""
from pathlib import Path
import struct,unittest
from diagnose_v134_sc_sda_writers import STATUS_DISP,STATUS_READ_PC,scan_slots,describe
HERE=Path(__file__).resolve().parent

def word(op,reg,base,disp):
    return struct.pack(">I",(op<<26)|(reg<<21)|(base<<16)|(disp&0xffff))
class V134(unittest.TestCase):
    def test_sda_reads_and_writes_with_signed_offset(self):
        a=word(34,4,13,STATUS_DISP)
        b=word(38,4,13,STATUS_DISP)
        c=word(32,5,13,STATUS_DISP)
        d=word(38,4,12,STATUS_DISP)
        e=word(38,4,13,STATUS_DISP+1)
        sections=[(0,0,STATUS_READ_PC,bytearray(a+b+c+d+e)),
                  (1,0,0x80700000,bytearray(b))]
        sites=scan_slots(sections)
        self.assertEqual(len(sites),3)
        self.assertEqual([x["kind"] for x in sites],["read","write","read"])
        self.assertEqual(sites[0]["pc"],STATUS_READ_PC)
        self.assertEqual(sites[0]["op"],"lbz")
        self.assertEqual(sites[1]["op"],"stb")
        self.assertEqual(sites[0]["register"],4)
        self.assertIn("V134_SDA_XREF reads=2 writes=1 canonical=1",describe(sites)[0])
    def test_reject_unaligned_text(self):
        with self.assertRaises(ValueError):
            scan_slots([(0,0,STATUS_READ_PC,bytearray(b"123"))])
    def test_original_stays_private(self):
        s=(HERE/"diagnose_v134_sc_sda_writers.py").read_text()
        self.assertIn("hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA",s)
        self.assertNotIn("print(raw)",s)
        self.assertNotIn("print(word)",s)
        self.assertIn("V134_SDA_XREF result=failed",s)
if __name__=="__main__":unittest.main()
