import unittest
import hashlib
import struct
import tempfile
from pathlib import Path
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe
from prepare_v433_full_os_entry import patch_probe as os_probe
from prepare_v435_full_os_time import patch_probe as time_probe
from prepare_v439_full_os_hardware import (patch_probe,return_seam,expectations,install,
    BODIES,EDGES,EXEC,PERF,REGS,FP,STOP,PreparationError)
from prepare_v439_full_os_hardware import COPY as COPY_PC
from test_v435_full_os_time import fixture as time_fixture
from prepare_v435_full_os_time import EDGES as TIME_EDGES
from prepare_v433_full_os_entry import DB,OS
from prepare_v419_full_start import ENTRY,REG,HW,HEADER,TRACE,INTERPRET
from prepare_v425_full_hardware import ENTRIES,MICRO
from prepare_v428_full_cache import expectations as cache_expectations
from prepare_v430_full_data import expectations as data_expectations
from audit_v435_full_os_time import STAGES as TIME,RESULT as TIME_RESULT
from test_v435_full_os_time_audit import PREFIX
from audit_v439_full_os_hardware import STAGES,RESULT,COPY,inspect
HOST=Path(__file__).parent
def log(lines):return b'\n'.join(lines)+b'\n'
def put(data,pc,word):
    for i in range(7):
        off,base,size=(struct.unpack_from('>I',data,h+4*i)[0] for h in (0,0x48,0x90))
        if size and base<=pc and pc+4<=base+size:
            struct.pack_into('>I',data,off+pc-base,word);return
    raise ValueError('fixture range')
def fixture():
    data=bytearray(time_fixture())
    for pc,n in BODIES:
        put(data,pc,0x60000000);put(data,pc+4*(n-1),0x4e800020)
    for site,target in EDGES:put(data,site,0x48000001|((target-site)&0x03fffffc))
    put(data,EXEC+20,0x48000000|((COPY_PC-EXEC-20)&0x03fffffc))
    for i,reg in enumerate(REGS):
        put(data,PERF+8*i,(31<<26)|(3<<21)|((reg&31)<<16)|((reg>>5)<<11)|(467<<1))
    put(data,FP,(63<<26)|(29<<21)|(38<<1))
    put(data,STOP,0x60000000)
    return bytes(data)
def digest(data):return hashlib.sha256(data).hexdigest()
def trace(pc):return f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);'

class Tests(unittest.TestCase):
    def test_geometry_and_diagnostics(self):
        raw=fixture()
        header,word=expectations(raw,digest(raw))
        self.assertEqual(header.count('OsTimeEdge{'),12)
        self.assertEqual(word,0x60000000)
        for pc,stage,ordinal in ((BODIES[0][0]+4*(BODIES[0][1]-1),'helper_return',1),
                (EXEC+20,'exec_tail',0),(PERF,'performance_helper',1),(FP,'fp_helper',0),
                (EDGES[0][0],'call_geometry',1)):
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(PreparationError) as e:expectations(bad,digest(bad))
            self.assertEqual((e.exception.stage,e.exception.ordinal),(stage,ordinal))
    def test_full_install_and_missing_trace(self):
        raw=fixture();sha=digest(raw)
        _,ct=cache_expectations(raw,sha);_,dt,w=data_expectations(raw,sha)
        pcs={ENTRY,REG,HW,DB,OS,*[e[0] for e in ENTRIES]}|ct|dt|{p for _,p in TIME_EDGES}|{p for _,p in EDGES}|{COPY_PC}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);rt=root/'nWiiRuntime';stubs=rt/'src/core/os_hle_stubs.cpp';interp=rt/'src/hle/interpreter.cpp';dest=rt/'include'
            dest.mkdir(parents=True);stubs.parent.mkdir(parents=True);interp.parent.mkdir(parents=True)
            stubs.write_text(HEADER+'\n'+TRACE+'\n}');interp.write_text(HEADER+'\n'+INTERPRET+'\n}\n'+MICRO+'\n}')
            seam='\nloc_80004058: ;\n    // 0x80004058: '+f'{w:08X}'+'\nloc_80520700: ;\n    // 0x80520700: 60000000\n'
            source='\n'.join(trace(pc) for pc in sorted(pcs))+seam
            shard=root/'output_0.cpp'
            for content,stage in ((source.replace(trace(EXEC),''),'trace_missing'),(source+'\n'+trace(EXEC),'trace_duplicate')):
                shard.write_text(content)
                with self.assertRaises(PreparationError) as e:install(raw,root,HOST,sha)
                self.assertEqual((e.exception.stage,e.exception.ordinal),(stage,1))
                self.assertFalse((dest/'undercover').exists())
            shard.write_text(source);install(raw,root,HOST,sha)
            self.assertIn('V430 original data return',shard.read_text())
            self.assertIn('V439 original hardware return',shard.read_text())
            self.assertEqual((dest/'undercover/wii_full_start_probe_v419.h').read_text().count('std::_Exit(0)'),1)

    def test_probe(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for transform in (cache_probe,data_probe,os_probe,time_probe):
            old=transform(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('os_hw.begin(cpu)',new);self.assertIn('os_hw.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
        seam='loc_80520700: ;\n    // 0x80520700: 60000000\n'
        self.assertIn('trace_call(0x80520700, ctx)',return_seam(seam,0x60000000))
        for bad in (seam+seam,seam.replace('60000000','4E800020'),return_seam(seam,0x60000000)):
            with self.assertRaises(ValueError):return_seam(bad,0x60000000)
    def test_gate(self):
        prefix=PREFIX+TIME+[TIME_RESULT]
        for copy in (0,1):
            begin=f'V439_HW_BEGIN copy={copy}'.encode()
            tail=[begin]+STAGES[:1]+([COPY] if copy else [])+STAGES[1:]+[RESULT]
            good=prefix+tail
            self.assertTrue(inspect(log(good),0)[1])
            for bad,rc in ((good,88),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(good+[COPY],0),(prefix+tail[:1]+tail[2:],0)):
                self.assertFalse(inspect(log(bad),rc)[1])
            self.assertIn('reason=7',inspect(log(prefix+tail[:2]+[b'V439_HW_INVALID reason=7 stage=1']),88)[0])
if __name__=='__main__':unittest.main()
