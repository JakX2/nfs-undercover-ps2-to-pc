#!/usr/bin/env python3
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from prepare_v419_full_start import ENTRY,REG,HW,HEADER,TRACE,INTERPRET
from prepare_v425_full_hardware import ENTRIES,MICRO
from test_v425_full_hardware import fixture as hardware_fixture
from prepare_v428_full_cache import ALLOWED,CACHE,ERROR,ERROR_CALLS,DATA,DATA_LR,expectations,install,patch_probe
from audit_v428_full_cache import STAGES,RESULT,inspect
HOST=Path(__file__).parent

def fixture():
    original=hardware_fixture();regions=[(0x80004000,bytearray(0x400)),(0x804b7900,bytearray(0x80526600-0x804b7900))]
    def put(pc,raw):
        for base,region in regions:
            if base<=pc and pc+len(raw)<=base+len(region):region[pc-base:pc-base+len(raw)]=raw;return
        raise ValueError('synthetic range')
    def word(pc,w):put(pc,struct.pack('>I',w))
    def bl(pc,dest):word(pc,0x48000001|((dest-pc)&0x03fffffc))
    for i in range(7):
        off,base,size=(struct.unpack_from('>I',original,b+4*i)[0] for b in (0,0x48,0x90))
        if size:put(base,original[off:off+size])
    for i,t in enumerate(sorted(ALLOWED)*3):
        if i<26:bl(CACHE+4*i,t)
    word(CACHE+77*4,0x4e800020);word(ERROR+161*4,0x4e800020)
    for s,t in ERROR_CALLS:bl(s,t)
    bl(DATA_LR-4,DATA)
    for t in ALLOWED|{t for _,t in ERROR_CALLS}|{DATA}:word(t,0x60000000)
    # Restore the first cache BL after writing helper entry words; CACHE is not a target.
    out=bytearray(256)
    for i,(base,raw) in enumerate(regions):
        for b,v in ((0,len(out)),(0x48,base),(0x90,len(raw))):struct.pack_into('>I',out,b+4*i,v)
        out.extend(raw)
    struct.pack_into('>I',out,0xe0,ENTRY);return bytes(out)

class Tests(unittest.TestCase):
    def test_geometry(self):
        data=fixture();sha=hashlib.sha256(data).hexdigest();header,targets=expectations(data,sha)
        self.assertEqual(header.count('CacheEdge{'),29);self.assertEqual(len(targets),12)
        with self.assertRaises(ValueError):expectations(data)
        bad=bytearray(data);bad[256+0x400+CACHE-0x804b7900]^=1
        with self.assertRaises(ValueError):expectations(bad,hashlib.sha256(bad).hexdigest())
    def test_install(self):
        data=fixture();sha=hashlib.sha256(data).hexdigest();_,targets=expectations(data,sha)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rt=root/'nWiiRuntime';stubs=rt/'src/core/os_hle_stubs.cpp';interp=rt/'src/hle/interpreter.cpp';dest=rt/'include'
            dest.mkdir(parents=True);stubs.parent.mkdir(parents=True);interp.parent.mkdir(parents=True)
            stubs.write_text(HEADER+'\n'+TRACE+'\n}');interp.write_text(HEADER+'\n'+INTERPRET+'\n}\n'+MICRO+'\n}')
            shard=root/'output_0.cpp';source='\n'.join(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);' for pc in sorted({ENTRY,REG,HW,*[e[0] for e in ENTRIES]}|targets))
            shard.write_text(source+'\n'+source)
            with self.assertRaises(ValueError):install(data,root,HOST,sha)
            self.assertFalse((dest/'undercover').exists());shard.write_text(source);install(data,root,HOST,sha)
            self.assertIn('cache.observe(addr,cpu)',(dest/'undercover/wii_full_start_probe_v419.h').read_text());self.assertEqual(shard.read_text(),source)
            with self.assertRaises(ValueError):install(data,root,HOST,sha)
    def test_gate(self):
        good=b'\n'.join(STAGES+[RESULT])+b'\n';self.assertTrue(inspect(good,0)[1])
        for raw,rc in ((good,84),(good+RESULT,0),(good.replace(STAGES[10],STAGES[9]),0),(good+b'V425_HARDWARE_FALLBACK hit=1\n',0),(b'\n'.join(STAGES),0)):
            self.assertFalse(inspect(raw,rc)[1])
        row,ok=inspect(b'\n'.join(STAGES[:9]+[b'V428_CACHE_INVALID reason=4 stage=0 calls=3']),84)
        self.assertFalse(ok);self.assertIn('hardware=9 cache=0 fallback=0 reason=4 calls=3',row)
    def test_probe_seam(self):
        source=(HOST/'wii_full_hardware_probe_v425.h').read_text();p=patch_probe(source)
        self.assertIn('cache.begin(cpu)',p)
        with self.assertRaises(ValueError):patch_probe(p)
if __name__=='__main__':unittest.main()
