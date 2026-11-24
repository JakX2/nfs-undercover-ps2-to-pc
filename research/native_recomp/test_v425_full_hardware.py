#!/usr/bin/env python3
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from prepare_v419_full_start import ENTRY,REG,HW,HEADER,TRACE,INTERPRET
from prepare_v425_full_hardware import PS,HIDR,HIDW,IC,FPR,CACHE,ENTRIES,MICRO,hardware_expectations,install
from audit_v425_full_hardware import STAGES,RESULT,inspect
HOST=Path(__file__).parent

def fixture():
    def bl(pc,target):return 0x48000001|((target-pc)&0x03fffffc)
    def words(n):return [0x60000000]*(n-1)+[0x4e800020]
    low=bytearray((HW+36-ENTRY));reg=words(36);hw=words(9);ps=words(21);fpr=words(74)
    for i,t in ((4,PS),(5,FPR),(6,CACHE)):hw[i]=bl(HW+4*i,t)
    for i,t in ((3,HIDR),(5,HIDW),(6,IC)):ps[i]=bl(PS+4*i,t)
    fpr[8]=56<<26;fpr[40]=50<<26;fpr[72]=(63<<26)|(711<<1)
    for pc,w in ((ENTRY,[bl(ENTRY,REG),bl(ENTRY+4,HW)]),(REG,reg),(HW,hw)):struct.pack_into('>'+str(len(w))+'I',low,pc-ENTRY,*w)
    out=bytearray(256)
    parts=[(ENTRY,low)]+[(pc,struct.pack('>'+str(len(w))+'I',*w)) for pc,w in ((PS,ps),(HIDR,words(2)+words(2)),(IC,words(4)),(FPR,fpr),(CACHE,words(4)))]
    for i,(pc,data) in enumerate(parts):
        for b,v in ((0,len(out)),(0x48,pc),(0x90,len(data))):struct.pack_into('>I',out,b+4*i,v)
        out.extend(data)
    struct.pack_into('>I',out,0xe0,ENTRY);return bytes(out)
class Tests(unittest.TestCase):
    def test_digest_and_call_geometry(self):
        data=fixture();sha=hashlib.sha256(data).hexdigest()
        self.assertIn('HardwareExpectations expected_hardware',hardware_expectations(data,sha))
        with self.assertRaises(ValueError):hardware_expectations(data)
        broken=bytearray(data);broken[256+HW-ENTRY+16]^=1
        with self.assertRaises(ValueError):hardware_expectations(broken,hashlib.sha256(broken).hexdigest())
    def test_stage_install_and_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rt=root/'nWiiRuntime';stubs=rt/'src/core/os_hle_stubs.cpp';interp=rt/'src/hle/interpreter.cpp';dest=rt/'include'
            dest.mkdir(parents=True);stubs.parent.mkdir(parents=True);interp.parent.mkdir(parents=True)
            stubs.write_text(HEADER+'\n'+TRACE+'\n}');interp.write_text(HEADER+'\n'+INTERPRET+'\n}\n'+MICRO+'\n}')
            shard=root/'output_0.cpp';source='\n'.join(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);' for pc in (ENTRY,REG,HW,*[e[0] for e in ENTRIES]))
            data=fixture();sha=hashlib.sha256(data).hexdigest();shard.write_text(source+'\n'+source)
            with self.assertRaises(ValueError):install(data,root,HOST,sha)
            self.assertFalse((dest/'undercover').exists());shard.write_text(source);install(data,root,HOST,sha)
            self.assertIn('micro_interpret(CPUContext& ctx, uint32_t opcode, uint32_t pc) {\n  if',interp.read_text())
            self.assertTrue((dest/'undercover/v425_private_hardware_expectations.h').exists());self.assertEqual(shard.read_text(),source)
            with self.assertRaises(ValueError):install(data,root,HOST,sha)
    def test_gate(self):
        good=b'\n'.join(STAGES+[RESULT])+b'\n';self.assertTrue(inspect(good,0)[1])
        for bad,rc in ((good,124),(good+RESULT,0),(good.replace(STAGES[6],STAGES[5]),0),(good+b'V425_HARDWARE_FALLBACK hit=1\n',0),(b'\n'.join(STAGES),0)):
            self.assertFalse(inspect(bad,rc)[1])
        self.assertIn('stages=4 fallback=1',inspect(b'\n'.join(STAGES[:4]+[b'V425_HARDWARE_FALLBACK hit=1']),83)[0])
if __name__=='__main__':unittest.main()
