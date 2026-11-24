#!/usr/bin/env python3
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v413_nand_context_resume import (patch,CAPS,INCLUDE,STATE,RESET,HEAD,PENDING,TRACE_NEXT,TRIAL_NEXT,EXIT_OBSERVER,RESUME)
from audit_v413_nand_context_resume import inspect

# All source seams here are independently authored host observer fragments.
SOURCE='\n'.join([INCLUDE,STATE,RESET,HEAD,PENDING,TRACE_NEXT,TRIAL_NEXT,EXIT_OBSERVER,RESUME]+
                [old for old,_,count in CAPS for _ in range(count)])
RETIRED='V412_LEGACY_FRONTIER continued=1\n'
PREFIX='V413_CONTEXT_PREFIX verified=1\n'
LOAD='V413_CONTEXT_LOAD mapped=1\n'
RESTORE='V413_CONTEXT_RESTORE regs=1 msr=1 coherent=1 interrupted=1\n'
EXIT='V413_CONTEXT_EXIT calls=192 prefix=1 load=1 mapped=1 hit=1 restored=1 interrupted=1 matched=1\n'
TRIAL='V413_CONTEXT_TRIAL complete=1\n'
SAMPLE=LOAD+RESTORE+RETIRED+PREFIX+EXIT+TRIAL
CPP=r'''
#include "wii_v413_context_witness.h"
#include <map>
using undercover::wii::NandContextWitness;
struct Mmu {
    std::map<uint32_t,uint32_t> mem;
    uint32_t* get_ptr(uint32_t a){auto i=mem.find(a&~3u);return i==mem.end()?nullptr:&i->second;}
    uint32_t read32(uint32_t a){return mem.at(a);}
};
struct Cpu {
    std::array<uint32_t,32> gpr{};
    uint32_t pc=0,msr=0,lr=0,ctr=0,xer=0;
    uint64_t inst_count=10;
    Mmu mmu;
};
int main(){
    constexpr uint32_t base=0x80010000u,pc=0x80020000u;
    Cpu c; c.gpr[3]=base;
    for(uint32_t i=0;i<416u;i+=4u)c.mmu.mem[base+i]=i;
    c.mmu.mem[base+408u]=pc;c.mmu.mem[base+412u]=0x8000u;c.mmu.mem[pc]=0;
    NandContextWitness w;
    if(!w.capture(c,pc,0x8000u,true)||!w.mapped||!w.interrupted||w.restored())return 1;
    if(w.capture(c,pc,0x8000u,true))return 2;
    c.pc=pc;c.msr=0x8000u;c.lr=132;c.ctr=136;c.xer=140;
    for(unsigned i=0;i<32u;++i)c.gpr[i]=4u*i;
    if(w.observe(c,true))return 3; // same instruction count
    ++c.inst_count;
    if(!w.observe(c,true)||!w.restored()||w.observe(c,true))return 4;
    c.gpr[3]=base;NandContextWitness bad;
    c.mmu.mem.erase(base+16u);
    if(!bad.capture(c,pc,0x8000u,true)||bad.mapped||bad.observe(c,true))return 5;
    c.mmu.mem[base+16u]=16;
    NandContextWitness mismatch;
    mismatch.capture(c,pc,0x8000u,true);++c.inst_count;
    if(!mismatch.observe(c,true)||mismatch.restored())return 6;
    NandContextWitness unmasked;
    if(!unmasked.capture(c,pc,0x8000u,false)||unmasked.mapped)return 7;
    if(NandContextWitness::context_range(0xfffffffcu)||NandContextWitness::context_range(0x81800000u-412u))return 8;
    return 0;
}
'''
class Tests(unittest.TestCase):
    def test_seams(self):
        result=patch(SOURCE)
        self.assertIn('if(owned||v396_calls==192u){',result)
        self.assertIn(RESUME,result)
        self.assertIn(TRACE_NEXT,result)
        self.assertIn('v396_calls>=96u?48u:',result)
        for old in (INCLUDE,STATE,RESET,HEAD,PENDING,TRACE_NEXT,TRIAL_NEXT,EXIT_OBSERVER,RESUME):
            with self.subTest(old=old[:30]),self.assertRaises(ValueError):patch(SOURCE.replace(old,'missing',1))
        with self.assertRaises(ValueError):patch(result)
    def test_cpp_witness(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('g++ unavailable')
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'fixture.cpp';exe=Path(td)/'fixture';src.write_text(CPP)
            p=subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror','-I',str(Path(__file__).parent),str(src),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(subprocess.run([str(exe)],timeout=5).returncode,0)
    def test_gate(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'private.log'
            def audit(data,rc=0):
                path.write_text(data);return inspect(path,rc)
            self.assertIn('verified=1 context_verified=1 interrupted_verified=1',audit(SAMPLE*16))
            no_load=RETIRED+PREFIX+EXIT.replace('load=1 mapped=1 hit=1 restored=1 interrupted=1','load=0 mapped=0 hit=0 restored=0 interrupted=0')+TRIAL
            self.assertIn('verified=1 context_verified=0 interrupted_verified=0',audit(no_load*16))
            for broken in (SAMPLE*15,SAMPLE*17,SAMPLE*16+LOAD,(SAMPLE.replace(RESTORE,''))*16,(SAMPLE.replace('calls=192','calls=96'))*16,(SAMPLE.replace('matched=1','matched=0'))*16):
                self.assertIn(' verified=0 ',audit(broken))
            self.assertIn(' verified=0 ',audit(SAMPLE*16,134))
if __name__=='__main__':unittest.main()
