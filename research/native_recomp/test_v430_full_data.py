#!/usr/bin/env python3
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from prepare_v419_full_start import ENTRY,REG,HW,HEADER,TRACE,INTERPRET
from prepare_v425_full_hardware import ENTRIES,MICRO
from prepare_v428_full_cache import expectations as cache_expectations
from test_v428_full_cache import fixture as cache_fixture
from prepare_v430_full_data import expectations,install,return_seam,CALLS,COUNTS,RETURN,TABLE
from audit_v430_full_data import CACHE,HELPERS,RESULT,inspect
HOST=Path(__file__).parent

def fixture():
    old=cache_fixture();raw=bytearray(old[:256]);sections=[]
    for i in range(7):
        off,base,size=(struct.unpack_from('>I',old,b+4*i)[0] for b in (0,0x48,0x90))
        if size:sections.append((base,bytearray(old[off:off+size])))
    sections[0][1].extend(bytearray(0x80006500-0x80004400))
    def put(pc,word):
        for base,section in sections:
            if base<=pc and pc+4<=base+len(section):struct.pack_into('>I',section,pc-base,word);return
        raise ValueError('range')
    for pc,n in COUNTS:
        put(pc,0x60000000);put(pc+4*(n-1),0x4e800020)
    for site,target in CALLS:put(site,0x48000001|((target-site)&0x03fffffc))
    put(RETURN,0x60000000)
    for i in range(11):
        for j,w in enumerate((0x80008000+0x100*i,0x80008000+0x100*i,0x100)):put(TABLE+12*i+4*j,w)
    for i,(a,n) in enumerate(((0x80010000,950236),(0x80110000,13164),(0x80120000,56))):put(TABLE+0x90+8*i,a);put(TABLE+0x94+8*i,n)
    for i,(base,sec) in enumerate(sections):
        for b,v in ((0,len(raw)),(0x48,base),(0x90,len(sec))):struct.pack_into('>I',raw,b+4*i,v)
        raw.extend(sec)
    return bytes(raw)
class Tests(unittest.TestCase):
    def test_geometry(self):
        data=fixture();sha=hashlib.sha256(data).hexdigest();h,targets,w=expectations(data,sha)
        self.assertEqual(h.count('DataRange{'),3);self.assertEqual(len(targets),2);self.assertEqual(w,0x60000000)
        with self.assertRaises(ValueError):expectations(data)
        for pc in (TABLE+4,TABLE+0x94,CALLS[2][0]):
            bad=bytearray(data);bad[256+pc-0x80004000]^=1
            with self.assertRaises(ValueError):expectations(bad,hashlib.sha256(bad).hexdigest())
    def test_return_seam(self):
        src='loc_80004058: ;\n    // 0x80004058: 60000000\n'
        p=return_seam(src,0x60000000);self.assertIn('V430 original data return',p)
        for bad in (src+src,src.replace('60000000','12345678'),p):
            with self.assertRaises(ValueError):return_seam(bad,0x60000000)
    def test_install(self):
        data=fixture();sha=hashlib.sha256(data).hexdigest();_,targets,w=expectations(data,sha);_,cache_targets=cache_expectations(data,sha)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rt=root/'nWiiRuntime';stubs=rt/'src/core/os_hle_stubs.cpp';interp=rt/'src/hle/interpreter.cpp';dest=rt/'include'
            dest.mkdir(parents=True);stubs.parent.mkdir(parents=True);interp.parent.mkdir(parents=True)
            stubs.write_text(HEADER+'\n'+TRACE+'\n}');interp.write_text(HEADER+'\n'+INTERPRET+'\n}\n'+MICRO+'\n}')
            shard=root/'output_0.cpp';source='\n'.join(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);' for pc in sorted({ENTRY,REG,HW,*[e[0] for e in ENTRIES]}|targets|cache_targets))+'\nloc_80004058: ;\n    // 0x80004058: 60000000\n'
            shard.write_text(source+source)
            with self.assertRaises(ValueError):install(data,root,HOST,sha)
            self.assertFalse((dest/'undercover').exists());shard.write_text(source);install(data,root,HOST,sha)
            self.assertEqual(shard.read_text(),return_seam(source,w));self.assertIn('data.finish(cpu)',(dest/'undercover/wii_full_start_probe_v419.h').read_text())
            with self.assertRaises(ValueError):install(data,root,HOST,sha)
    def test_gate(self):
        good=b'\n'.join(CACHE+[b'V430_DATA_BEGIN before_nonzero=4']+HELPERS+[RESULT])+b'\n';self.assertTrue(inspect(good,0)[1])
        for raw,rc in ((good,85),(good+RESULT,0),(good.replace(HELPERS[1],HELPERS[0]),0),(good.replace(b'nonzero=4',b'nonzero=963457'),0),(good+b'V425_HARDWARE_FALLBACK hit=1\n',0),(b'\n'.join(CACHE),0)):
            self.assertFalse(inspect(raw,rc)[1])
        self.assertIn('helpers=2',inspect(b'\n'.join(CACHE+[b'V430_DATA_BEGIN before_nonzero=4']+HELPERS[:2]+[b'V430_DATA_INVALID reason=4 calls=2']),85)[0])
if __name__=='__main__':unittest.main()
