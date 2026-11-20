#!/usr/bin/env python3
"""V132 owner-free synthetic status assignment and call-graph tests."""
import struct,unittest
from pathlib import Path
from diagnose_v132_sc_status import (
  ENTRY,SIZE,DISABLE_AT,RESTORE_AT,DISABLE_DEST,RESTORE_DEST,
  inspect,report,format_site_list,
)
from make_osinit_execparams_v28 import BLR,NOP
HERE=Path(__file__).resolve().parent

def makeword(pc,dest):
    disp=(dest-pc)&0x03fffffc
    return (18<<26)|disp|1

def synthetic():
    arr=[NOP]*(SIZE//4)
    arr[0]=0x9421FFF0
    arr[(DISABLE_AT-ENTRY)//4]=makeword(DISABLE_AT,DISABLE_DEST)
    arr[(RESTORE_AT-ENTRY)//4]=makeword(RESTORE_AT,RESTORE_DEST)
    arr[12]=(14<<26)|(3<<21)|1
    arr[13]=(14<<26)|(3<<21)
    arr[14]=(14<<26)|(3<<21)|0xFFFF
    arr[22]=(32<<26)|(3<<21)|(13<<16)|0xFFF0
    arr[-1]=BLR
    return struct.pack(">"+("I"*len(arr)),*arr)

class V132(unittest.TestCase):
    def test_call_edges_return_assignments_and_sda(self):
        obj=inspect(synthetic())
        self.assertEqual(obj["disable"],1)
        self.assertEqual(obj["restore"],1)
        self.assertEqual(obj["calls"],2)
        self.assertEqual(obj["li1"],1)
        self.assertEqual(obj["li0"],1)
        self.assertEqual(obj["lim1"],1)
        self.assertEqual(obj["sda_reads"],1)
        self.assertEqual(obj["sda_sites"][0][-1],-16)
        self.assertIn("V132_SC_STATUS disable=1 restore=1",report(obj))
        line="\n".join(format_site_list(obj))
        self.assertIn("V132_STATUS_ASSIGN kind=li1_sites",line)
        self.assertIn("V132_STATUS_SDA",line)
    def test_malformed_owner_region_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect(synthetic()[:-4])
        data=bytearray(synthetic())
        data[-4:]=struct.pack(">I",NOP)
        with self.assertRaises(ValueError):
            inspect(bytes(data))
    def test_authenticator_and_source_privacy(self):
        src=(HERE/"diagnose_v132_sc_status.py").read_text()
        self.assertIn("hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA",src)
        self.assertNotIn("print(words)",src)
        self.assertNotIn("print(body)",src)
        self.assertIn("V132_SC_STATUS result=failed",src)
if __name__=="__main__":
    unittest.main()
