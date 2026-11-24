#!/usr/bin/env python3
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from prepare_v419_full_start import ENTRY,REG,HW,HEADER,TRACE,INTERPRET
from prepare_v425_full_hardware import ENTRIES,MICRO
from prepare_v428_full_cache import expectations as cache_expectations
from prepare_v430_full_data import expectations as data_expectations
from test_v430_full_data import fixture as data_fixture
from prepare_v433_full_os_entry import DB,OS,DB_CALL,OS_CALL,expectations,install
from audit_v430_full_data import CACHE,HELPERS,RESULT as DATA_RESULT
from audit_v433_full_os_entry import DB as DB_MARKER,RESULT,inspect
HOST=Path(__file__).parent
def fixture():
    data=bytearray(data_fixture())
    def put(pc,word):
        for i in range(7):
            off,base,size=(struct.unpack_from('>I',data,b+4*i)[0] for b in (0,0x48,0x90))
            if base<=pc and pc+4<=base+size:
                struct.pack_into('>I',data,off+pc-base,word);return
        raise ValueError('range')
    for site,target in ((DB_CALL,DB),(OS_CALL,OS)):
        put(site,0x48000001|((target-site)&0x03fffffc))
    put(DB,0x60000000);put(DB+36,0x4e800020);put(OS,0x60000000)
    return bytes(data)

class Tests(unittest.TestCase):
    def test_geometry(self):
        raw=fixture();sha=hashlib.sha256(raw).hexdigest()
        self.assertIn('expected_os',expectations(raw,sha))
        with self.assertRaises(ValueError):expectations(raw)
        bad=bytearray(raw)
        struct.pack_into('>I',bad,256+DB_CALL-0x80004000,0x60000000)
        with self.assertRaises(ValueError):expectations(bad,hashlib.sha256(bad).hexdigest())
    def test_install(self):
        raw=fixture();sha=hashlib.sha256(raw).hexdigest();_,ct=cache_expectations(raw,sha);_,dt,w=data_expectations(raw,sha)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rt=root/'nWiiRuntime';stubs=rt/'src/core/os_hle_stubs.cpp';interp=rt/'src/hle/interpreter.cpp';dest=rt/'include'
            dest.mkdir(parents=True);stubs.parent.mkdir(parents=True);interp.parent.mkdir(parents=True)
            stubs.write_text(HEADER+'\n'+TRACE+'\n}');interp.write_text(HEADER+'\n'+INTERPRET+'\n}\n'+MICRO+'\n}')
            trace=lambda pc:f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);'
            base='\n'.join(trace(pc) for pc in sorted({ENTRY,REG,HW,*[e[0] for e in ENTRIES]}|ct|dt))+'\nloc_80004058: ;\n    // 0x80004058: '+f'{w:08X}'+'\n'
            shard=root/'output_0.cpp';shard.write_text(base+trace(DB)+'\n')
            with self.assertRaises(ValueError):install(raw,root,HOST,sha)
            self.assertFalse((dest/'undercover').exists())
            shard.write_text(base+trace(DB)+'\n'+trace(OS)+'\n')
            install(raw,root,HOST,sha)
            probe=(dest/'undercover/wii_full_start_probe_v419.h').read_text()
            self.assertIn('os_entry.begin(cpu)',probe);self.assertIn('os_entry.observe(addr,cpu)',probe)
            self.assertEqual(probe.count('std::_Exit(0)'),1)
            with self.assertRaises(ValueError):install(raw,root,HOST,sha)
    def test_gate(self):
        prefix=b'\n'.join(CACHE+[b'V430_DATA_BEGIN before_nonzero=0']+HELPERS+[DATA_RESULT])+b'\n'
        for arena in (0,1):
            for info in (0,1):
                begin=f'V433_OS_BEGIN arena_hi_nonzero={arena} boot_info_nonzero={info}'.encode()
                good=prefix+b'\n'.join((begin,DB_MARKER,RESULT))+b'\n'
                self.assertTrue(inspect(good,0)[1])
                for bad,rc in ((good,86),(good+RESULT,0),(good.replace(DB_MARKER,RESULT),0),(good.replace(DATA_RESULT,b''),0),(good+b'V425_HARDWARE_FALLBACK hit=1\n',0),(prefix+begin+b'\n',0)):
                    self.assertFalse(inspect(bad,rc)[1])
        self.assertIn('reason=3',inspect(prefix+b'V433_OS_BEGIN arena_hi_nonzero=1 boot_info_nonzero=0\nV433_OS_INVALID reason=3 stage=1\n',86)[0])
if __name__=='__main__':unittest.main()
