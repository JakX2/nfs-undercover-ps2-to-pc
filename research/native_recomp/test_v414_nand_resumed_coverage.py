#!/usr/bin/env python3
import struct
import unittest
from test_v413_nand_context_resume import SOURCE
from derive_v413_nand_context_resume import patch as prior
from derive_v414_nand_resumed_coverage import patch,SEAM,TRACE,OBSERVE,OBSERVE_NEW
from audit_v414_nand_resumed_coverage import parse_trace,inspect,classify,RESTORE,TRIAL,NOP

A=0x80401000;B=A+16;C=B+16
BODY=bytes.fromhex('386000014e800020386000024e800020')
def dol(code):
    out=bytearray(256)
    for off,v in ((0,256),(0x48,A),(0x90,len(code)),(0xe0,A)):struct.pack_into('>I',out,off,v)
    return bytes(out)+code

def trace(*pcs):
    start=192-len(pcs)
    return RESTORE+b'\n'+f'V414_RESUMED_BEGIN after={start}\n'.encode()+b''.join(
        f'V414_RESUMED_ENTRY call={i} pc={pc:08x}\n'.encode() for i,pc in enumerate(pcs,start+1))+TRIAL+b'\n'

class Tests(unittest.TestCase):
    def test_reversible_patch(self):
        source=prior(SOURCE+'\n'+SEAM)
        result=patch(source)
        self.assertEqual(result.replace(SEAM+TRACE,SEAM,1).replace(OBSERVE_NEW,OBSERVE,1),source)
        self.assertIn('V414_RESUMED_BEGIN after=',result)
        for invalid in (source.replace(SEAM,''),source.replace(OBSERVE,''),result):
            with self.assertRaises(ValueError):patch(invalid)
    def test_trace_order(self):
        t=trace(A,B,C)
        self.assertEqual(parse_trace(t*16),[(A,B,C)]*16)
        for bad in (t*15,t*17,t.replace(b'call=190',b'call=191')*16,
                    t.replace(b'after=189',b'after=188')*16,
                    t.replace(RESTORE,b'bad')*16,t.replace(b'80401000',b'80401001')*16):
            with self.assertRaises(ValueError):parse_trace(bad)
    def test_exact_nop_repair_and_unchanged_neighbor(self):
        owner=dol(BODY*3);fixture=dol(BODY+NOP*4+BODY);sizes={A:16,B:16,C:16}
        summary,repair=inspect(owner,fixture,sizes,[(A,B,C)]*16)
        self.assertIn('original=2 nop=1 modified=0 missing=0 unknown=0 first=nop repairable=1',summary)
        self.assertEqual(repair,owner)
        self.assertNotIn(f'{B:08x}',summary)
    def test_mixed_and_interior_never_restored(self):
        owner=dol(BODY*3);fixture=dol(BODY+NOP*3+BODY[-4:]+BODY);sizes={A:16,B:16,C:16}
        summary,repair=inspect(owner,fixture,sizes,[(B,C)]*16)
        self.assertIn('first=modified repairable=0',summary);self.assertIsNone(repair)
        fixture=dol(BODY+NOP*4+BODY)
        self.assertEqual(classify(owner,fixture,sizes,B+4),('nop',None))
        self.assertEqual(classify(owner,fixture,{A:16,C:16},B),('unknown',None))
        summary,repair=inspect(owner,fixture,{A:16,C:16},[(B,C)]*16)
        self.assertIsNone(repair);self.assertIn('first=unknown',summary)
    def test_no_repair_for_authentic(self):
        owner=dol(BODY*3)
        summary,repair=inspect(owner,owner,{A:16,B:16,C:16},[(A,B,C)]*16)
        self.assertIn('all_original=1',summary);self.assertIsNone(repair)
if __name__=='__main__':unittest.main()
