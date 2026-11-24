#!/usr/bin/env python3
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from prepare_v419_full_start import ENTRY,REG,HW,HEADER,TRACE,INTERPRET,prepare,expectations
from audit_v419_full_start import inspect,STAGES,RESULT

HOST=Path(__file__).parent

def dol_fixture():
    out=bytearray(256)
    def bl(pc,target):return 0x48000001|((target-pc)&0x03fffffc)
    parts=((ENTRY,[bl(ENTRY,REG),bl(ENTRY+4,HW)]),(REG,[0x60000000]*35+[0x4e800020]),(HW,[0x60000000]*4))
    for i,(pc,words) in enumerate(parts):
        for base,value in ((0,len(out)),(0x48,pc),(0x90,len(words)*4)):struct.pack_into('>I',out,base+4*i,value)
        out.extend(struct.pack('>'+str(len(words))+'I',*words))
    struct.pack_into('>I',out,0xe0,ENTRY)
    return bytes(out)

class Tests(unittest.TestCase):
    def test_digest_and_branch(self):
        data=dol_fixture();digest=hashlib.sha256(data).hexdigest()
        self.assertIn('FullStartExpectations expected',expectations(data,digest))
        with self.assertRaises(ValueError):expectations(data)
        for at in (256,260,264+35*4,0xe0):
            broken=bytearray(data);broken[at]^=1;broken=bytes(broken)
            with self.assertRaises(ValueError):expectations(broken,hashlib.sha256(broken).hexdigest())
    def test_patch_rejects_missing_aot_and_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rt=root/'nWiiRuntime';stubs=rt/'src/core/os_hle_stubs.cpp';interp=rt/'src/hle/interpreter.cpp';dest=rt/'include';dest.mkdir(parents=True);stubs.parent.mkdir(parents=True);interp.parent.mkdir(parents=True)
            stubs.write_text(HEADER+'\n'+TRACE+'\n}');interp.write_text(HEADER+'\n'+INTERPRET+'\n}')
            shard=root/'output_0.cpp'
            source='\n'.join(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);' for pc in (ENTRY,REG,HW))
            data=dol_fixture();digest=hashlib.sha256(data).hexdigest()
            shard.write_text(source+'\n'+source)
            with self.assertRaises(ValueError):prepare(data,root,HOST,digest)
            self.assertEqual(stubs.read_text(),HEADER+'\n'+TRACE+'\n}')
            shard.write_text(source);prepare(data,root,HOST,digest)
            self.assertIn('v419::observe',stubs.read_text());self.assertIn('v419::reject_interpreter',interp.read_text())
            self.assertTrue((dest/'undercover/v419_private_start_expectations.h').exists())
            self.assertEqual(shard.read_text(),source)
            with self.assertRaises(ValueError):prepare(data,root,HOST,digest)
    def test_gate_exact_order_and_failure(self):
        good=b'\n'.join(STAGES+[RESULT])+b'\n'
        row,ok=inspect(good,0);self.assertTrue(ok);self.assertIn('stages=3 fallback=0 malformed=0 verified=1',row)
        for bad,rc in ((good,134),(good,124),(good+RESULT,0),(good.replace(STAGES[1],STAGES[0]),0),(b'\n'.join(STAGES),0),(good+b'V419_FULL_START_FALLBACK hit=1\n',0),(good+b'V419_FULL_START_STAGE n=4 pc=deadbeef\n',0)):
            row,ok=inspect(bad,rc);self.assertFalse(ok);self.assertNotIn('deadbeef',row)
        row,ok=inspect(STAGES[0]+b'\nV419_FULL_START_FALLBACK hit=1\n',83);self.assertFalse(ok);self.assertIn('stages=1 fallback=1',row)
if __name__=='__main__':unittest.main()
