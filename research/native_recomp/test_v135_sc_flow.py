#!/usr/bin/env python3
"""V135 owner-free original SC control-flow and status-lock tests."""
import struct,unittest
from pathlib import Path
from diagnose_v135_sc_flow import ENTRY,SIZE,STATUS_LOAD,STATUS_CLEAR,STATUS_RESTORE,decode,report
from make_osinit_execparams_v28 import NOP,BLR
HERE=Path(__file__).resolve().parent
def branch(pc,dest):
    return (18<<26)|((dest-pc)&0x03fffffc)|1
def mem(op,reg,base,disp):
    return (op<<26)|(reg<<21)|(base<<16)|(disp&0xffff)
def synthetic():
    w=[NOP]*(SIZE//4)
    w[0]=0x9421fff0
    for pc,op,reg in ((STATUS_LOAD,34,29),(STATUS_CLEAR,38,0),(STATUS_RESTORE,38,29)):
        w[(pc-ENTRY)//4]=mem(op,reg,13,-3176)
    w[14]=mem(32,3,1,0)
    w[17]=mem(14,3,0,0)
    for index in range(20,32):
        pc=ENTRY+4*index
        w[index]=branch(pc,0x80530000+index*4)
    w[-1]=BLR
    return struct.pack(">"+"I"*len(w),*w)
class V135(unittest.TestCase):
    def test_verified_lock_and_callgraph(self):
        d=decode(synthetic())
        self.assertEqual(len(d["calls"]),12)
        self.assertEqual(len(d["r3"]),2)
        self.assertEqual((d["loadreg"],d["clearreg"],d["restorereg"]),(29,0,29))
        self.assertIn("V135_SC_GRAPH calls=12",report(d)[0])
        self.assertEqual(len([x for x in report(d) if x.startswith("V135_SC_CALL")]),12)
    def test_guard_rejects_wrong_status_instruction(self):
        b=bytearray(synthetic())
        at=STATUS_LOAD-ENTRY
        b[at:at+4]=mem(34,3,13,-3176).to_bytes(4,"big")
        with self.assertRaises(ValueError):
            decode(bytes(b))
        with self.assertRaises(ValueError):
            decode(synthetic()[:-4])
    def test_private_original_remains_private(self):
        s=(HERE/"diagnose_v135_sc_flow.py").read_text()
        self.assertIn("hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA",s)
        self.assertNotIn("print(raw)",s)
        self.assertNotIn("print(w)",s)
        self.assertIn("V135_SC_GRAPH result=failed",s)
if __name__=="__main__":
    unittest.main()
