#!/usr/bin/env python3
import unittest
import tempfile
from pathlib import Path
import shutil
import subprocess
from derive_v432_nand_nested_call import OWNED,STOP,GUARD,MARK,first_edge,patch,audit
PC=0x80501000;TARGET=0x80502000;LR=PC+24
WORDS=(0x60000000,)*5+(0x48000001|((TARGET-(PC+20))&0x03fffffc),)+(0x60000000,)*8+(0x4e800020,)
def entry(call,pc,lr,resumed=0):return f'V420_CB_ENTRY call={call} pc={pc:x} lr={lr:x} ew=0 lw=0 em=1 lm=1 resumed={resumed} sc=1 r3=0'.encode()
FIRST=entry(0,PC,0x80500004);SECOND=entry(1,TARGET,LR)
TRACE=b'\n'.join([FIRST]+[f'V427_NATIVE_STEP slot={i} inst={i+1}'.encode() for i in range(6)]+[SECOND])+b'\n'
SOURCE=OWNED+'\n'+STOP+'\n'+GUARD+'\nV420_CB_ENTRY call=\nV413_CONTEXT_TRIAL complete=\n'
class Tests(unittest.TestCase):
    def test_control_exact(self):
        self.assertEqual(first_edge(TRACE,PC,WORDS),(TARGET,LR))
        for bad in (TRACE.replace(SECOND,entry(1,TARGET,LR+4)),TRACE.replace(b'slot=5',b'slot=7'),TRACE.replace(FIRST,entry(0,TARGET,LR))):
            with self.assertRaises(ValueError):first_edge(bad,PC,WORDS)
    def test_patch_preserves_stop_and_guard(self):
        out=patch(SOURCE,PC,TARGET,LR);self.assertIn(STOP,out);self.assertIn(GUARD,out);self.assertIn('v396_calls==0u',out)
        for bad in (SOURCE+SOURCE,out,SOURCE.replace(GUARD,'')):
            with self.assertRaises(ValueError):patch(bad,PC,TARGET,LR)
    def test_partial_audit(self):
        raw=b'\n'.join([FIRST,MARK,SECOND,entry(2,TARGET+4,LR+8)])+b'\n'
        row=audit(raw,134,PC,TARGET,LR);self.assertIn('max_calls=2',row);self.assertIn('retired_exact=1',row);self.assertNotIn(f'{PC:x}',row)
        for bad in (raw.replace(SECOND,entry(1,TARGET,LR+4)),raw.replace(FIRST+b'\n',b''),raw.replace(MARK,MARK+b'\n'+MARK)):
            with self.assertRaises(ValueError):audit(bad,134,PC,TARGET,LR)
    def test_cpp_predicate(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        out=patch(SOURCE,PC,TARGET,LR);code=out[:out.index(STOP)]
        src='#include <iostream>\n#include <cstdint>\nstruct Witness{bool done;bool restored(){return done;}};\nbool owned(uint32_t v395_next_pc,uint32_t addr,uint32_t lr,unsigned v396_calls,unsigned v398_site_seen,unsigned v400_parent_site,bool restored){struct{uint32_t lr;}ctx{lr};Witness v413_context{restored};\n'+code+'return owned;}\n'
        src+=f'int main(){{constexpr uint32_t pc=0x{PC:x}u,t=0x{TARGET:x}u,lr=0x{LR:x}u;return owned(pc,t,lr,0,0,0,false)||!owned(pc,t+4,lr,0,0,0,false)||!owned(pc,t,lr+4,0,0,0,false)||!owned(pc,t,lr,1,0,0,false)||!owned(pc,t,lr,0,1,0,false)||!owned(pc,t,lr,0,0,1,false)||!owned(pc,t,lr,0,0,0,true);}}\n'
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'t.cpp';exe=Path(td)/'t';f.write_text(src);subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror',str(f),'-o',str(exe)],check=True,capture_output=True);r=subprocess.run([str(exe)],check=True,capture_output=True);self.assertEqual(r.stdout.count(MARK),1)
if __name__=='__main__':unittest.main()
