#!/usr/bin/env python3
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest
from trace_v427_restored_function import instrument,branch,abort_row,step_row,edges
PC=0x80501000
WORDS=(0x60000000,)*14+(0x4e800020,)
def source():
    out=f'void func_{PC:08X}(CPUContext& ctx) {{\n    nwii::runtime::trace_call(0x{PC:08X}, ctx);\n'
    for i,w in enumerate(WORDS):out+=f'    ++ctx.inst_count;\nloc_{PC+i*4:X}: ;\n    // 0x{PC+i*4:08X}: {w:08X}\n'
    return out+'}\n'+f'{{0x{PC:08X}, 0x{PC+60:08X}, func_{PC:08X}}},\n'
class Tests(unittest.TestCase):
    def test_reversible_and_conflict(self):
        src=source();p=instrument(src,PC,WORDS);self.assertEqual(p.count('V427_NATIVE_STEP'),15)
        for bad in (src.replace('60000000','12345678',1),src+src,p):
            with self.assertRaises(ValueError):instrument(bad,PC,WORDS)
    def test_branch_decode(self):
        self.assertEqual(branch(0x48000005,PC),('direct_link',PC+4))
        self.assertEqual(branch(0x4bfffff8,PC),('direct_tail',PC-8))
        self.assertEqual(branch(0x4182fffc,PC),('conditional',PC-4))
        self.assertEqual(branch(0x4e800020,PC),('return',None))
        self.assertEqual(branch(0x4e800421,PC),('indirect',None))
        self.assertEqual(branch(0x44000002,PC),('syscall',None))
    def test_private_abort_classification(self):
        a,b=abort_row(b'terminate called after throwing an instance of std::runtime_error\nwhat():  interpreter fallback\n','throw std::runtime_error("interpreter fallback");',134)
        self.assertIn('known=1 category=interpreter exception=runtime',a);self.assertIn('label=interpreter fallback',b)
        a,b=abort_row(b'what():  secret address 80501234\n','"known"',134)
        self.assertIn('known=0 category=unknown',a);self.assertNotIn('80501234',a+b)
    def test_trace_result_and_reject(self):
        line=f'V420_CB_ENTRY call=1 pc={PC:x} lr=80501004 ew=0 lw=0 em=1 lm=1 resumed=0 sc=1 r3=0\n'.encode()
        raw=b'V427_NATIVE_STEP slot=0 inst=1\n'+line+b'V427_NATIVE_STEP slot=0 inst=2\nV427_NATIVE_STEP slot=14 inst=15\n'
        row=step_row(raw,134,PC,WORDS);self.assertIn('entered=1 steps=2 prior_steps=1 last_slot=14 last_kind=return',row)
        self.assertNotIn(f'{PC:x}',row)
        for bad in (raw.replace(b'slot=14',b'slot=15'),raw.replace(b'inst=15',b'inst=1')):
            with self.assertRaises(ValueError):step_row(bad,134,PC,WORDS)
    def test_synthetic_cpp_observer(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        src=instrument(source(),PC,WORDS);src=src[:src.index(f'{{0x{PC:08X},')]
        head='#include <cstdint>\nstruct CPUContext{uint64_t inst_count=0;};\nnamespace nwii::runtime {void trace_call(uint32_t,CPUContext&){} }\n'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.cpp';exe=Path(td)/'test';p.write_text(head+src+f'int main(){{CPUContext c;func_{PC:08X}(c);return c.inst_count!=15;}}\n')
            subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror','-Wno-unused-label',str(p),'-o',str(exe)],check=True,capture_output=True)
            r=subprocess.run([str(exe)],check=True,capture_output=True);self.assertEqual(r.stderr.count(b'V427_NATIVE_STEP'),15)
if __name__=='__main__':unittest.main()
