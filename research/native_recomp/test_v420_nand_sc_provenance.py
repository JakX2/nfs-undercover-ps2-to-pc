#!/usr/bin/env python3
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from derive_v420_nand_sc_provenance import PAIRS,NEW,patch,HELPER
from audit_v420_nand_sc_provenance import Entry,parse,inspect,SC_ROUTE
from audit_v416_nand_wait_state import FIELDS
from audit_v414_nand_resumed_coverage import RESTORE,TRIAL,NOP
from test_v414_nand_resumed_coverage import dol,BODY,A,B,C

ROUTE=tuple(sorted(SC_ROUTE));START=17

def make_trial():
    result=[]
    for i in range(193):
        pc,lr=(A if i==0 else B,A+4) if i<=START else ROUTE[(i-START-1)%3]
        result.append(Entry(i,pc,lr,0x38600001,0x38600001,1,1,int(i>START),1,0))
    return tuple(result)

def encode(trial):
    out=[]
    for e in trial:
        if e.call==START+1:out.extend([RESTORE,f'V414_RESUMED_BEGIN after={START}'.encode()])
        out.append(f'V420_CB_ENTRY call={e.call} pc={e.pc:x} lr={e.lr:x} ew={e.ew:x} lw={e.lw:x} em={e.em} lm={e.lm} resumed={e.resumed} sc={e.sc} r3={e.r3}'.encode())
        if e.resumed:
            flags=dict.fromkeys(FIELDS,0);flags.update(mapped=1,reply=1,ee=1)
            out.extend([f'V414_RESUMED_ENTRY call={e.call} pc={e.pc:08x}'.encode(),
                (f'V416_WAIT_STATE call={e.call} lr={e.lr:x} inst={e.call*32} tb={e.call*32} '+' '.join(f'{k}={v}' for k,v in flags.items())).encode()])
    return b'\n'.join(out+[TRIAL])+b'\n'

class Tests(unittest.TestCase):
    def test_reversible(self):
        source='\n'.join(x for x,_ in PAIRS)+'\n'+NEW
        result=patch(source)
        for a,b in reversed(PAIRS):result=result.replace(b,a,1)
        self.assertEqual(result,source)
        for bad in (source+PAIRS[0][0],source.replace(PAIRS[1][0],''),patch(source)):
            with self.assertRaises(ValueError):patch(bad)
    def test_private_trace_order(self):
        t=make_trial();raw=encode(t)
        self.assertEqual(parse(raw*16),[t]*16)
        for bad in (raw.replace(b'call=0 ',b'call=1 ',1),raw.replace(b'resumed=0',b'resumed=1',1),raw.replace(b'V420_CB_ENTRY call=5 ',b'other call=5 ',1),raw.replace(b'V420_CB_ENTRY call=18 pc=',b'V420_CB_ENTRY call=18 pc=0',1),raw.replace(b'sc=1',b'sc=6',1)):
            with self.assertRaises(ValueError):parse(bad*16)
    def test_repair_and_live_correspondence(self):
        owner=dol(BODY*3);fixture=dol(BODY+NOP*4+BODY);sizes={A:16,B:16,C:16}
        t=tuple(replace(e,ew=0x60000000) if e.pc==B else e for e in make_trial())
        summary,candidate=inspect(owner,fixture,sizes,[t]*16)
        self.assertEqual(candidate,owner)
        self.assertIn('pre_unique=2 original=1 nop=1 modified=0 missing=0 unknown=0 first=nop repairable=1 sc_route=16 sc1=16 sc3=0',summary)
        self.assertIn('entry_fixture=16',summary)
        self.assertNotIn('60000000',summary)
        summary,candidate=inspect(owner,fixture,sizes,[make_trial()]*16)
        self.assertIsNone(candidate);self.assertIn('entry_live_original=16',summary)
    def test_mixed_span_and_unknown_route(self):
        owner=dol(BODY*3);fixture=dol(BODY+NOP*3+BODY[-4:]+BODY)
        t=tuple(replace(e,pc=C,sc=3) if e.resumed else e for e in make_trial())
        summary,candidate=inspect(owner,fixture,{A:16,B:16,C:16},[t]*16)
        self.assertIsNone(candidate);self.assertIn('first=modified repairable=0 sc_route=0 sc1=0 sc3=16',summary)
    def test_cpp_observer(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('g++ unavailable')
        src=r'''#include <array>
#include <cstdint>
#include <iostream>
struct Mmu { uint8_t *get_ptr(uint32_t a){static uint8_t b=0;return a>=0x80000000u&&a<0x81800000u?&b:nullptr;} uint32_t read32(uint32_t a){return a==0x80500000u?0x48000001u:0x60000000u;}uint8_t read8(uint32_t){return 1u;} };
struct CPUContext {std::array<uint32_t,32> gpr{};Mmu mmu;uint32_t lr=0x80500004u;};
'''+HELPER+r'''
int main(){CPUContext c;c.gpr[13]=0x80700000u;c.gpr[3]=0xffffffffu;v420_entry(c,0x80501000u,0u,false);c.gpr[13]=0u;c.lr=0u;v420_entry(c,0x80501000u,1u,true);}
'''
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.cpp';exe=Path(td)/'test';p.write_text(src)
            r=subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror',str(p),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('ew=60000000 lw=48000001 em=1 lm=1 resumed=0 sc=1 r3=2',r.stdout)
            self.assertIn('lw=0 em=1 lm=0 resumed=1 sc=5 r3=2',r.stdout)
if __name__=='__main__':unittest.main()
