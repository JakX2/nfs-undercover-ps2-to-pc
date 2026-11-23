#!/usr/bin/env python3
"""V401 synthetic source guards, PPC link-class arithmetic, and C++ checks."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v400_nand_parent_resume import Tests as Fixture400
from derive_v400_nand_parent_resume import patch as v400
from derive_v401_nand_linksite_classify import (
    patch, STATE, RESET, WORD, WORD_NEXT, STOP, STOP_NEXT, TRIAL,
    ENTRY, TRIAL_MARKER
)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture400.setUpClass()
        cls.prior=v400(Fixture400.prior)
    def test_original_guest_opcode_only_read_and_bounded(self):
        s=patch(self.prior)
        self.assertEqual(s.count(ENTRY),1)
        self.assertEqual(s.count(TRIAL_MARKER),1)
        self.assertIn('const uint32_t v399_call=ctx.mmu.read32(ctx.pc-4u);',WORD_NEXT)
        self.assertIn('v401_op==18u',WORD_NEXT)
        self.assertIn('v401_op==16u',WORD_NEXT)
        self.assertIn('v401_xo==528u',WORD_NEXT)
        self.assertIn('target==v395_next_pc',WORD_NEXT)
        self.assertIn('blr_verified=0',STOP_NEXT)
        self.assertIn('if(owned||v396_calls==24u)',s)
        self.assertIn('V400_NAND_PARENT_RESUME site=',s)
        self.assertIn('V399_NAND_RETURN_ORDER site=',s)
        self.assertLess(s.index('nwii::runtime::v401_kind=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
        for forbidden in ('ctx.pc=', 'ctx.lr=', 'ctx.msr=', 'ctx.gpr[3]=',
                          'ctx.mmu.write','service_one(','ipc70_bus.write32('):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(
                    r'\b'+re.escape(forbidden)+r'(?!=)',WORD_NEXT+STOP_NEXT))
            else:
                self.assertNotIn(forbidden,WORD_NEXT+STOP_NEXT)
    def test_ppc_direct_branch_target_arithmetic(self):
        def classify_and_target(word:int,pc:int):
            op=word>>26
            if not(word&1) or op not in (16,18):
                return None
            mask=0x03fffffc if op==18 else 0xfffc
            displacement=word&mask
            sign=0x02000000 if op==18 else 0x8000
            if displacement&sign:
                displacement|=0xfc000000 if op==18 else 0xffff0000
            target=(displacement if word&2 else
                    pc-4+displacement)&0xffffffff
            return target
        self.assertEqual(classify_and_target(0x48000009,0x804f0f54),0x804f0f58)
        self.assertEqual(classify_and_target(0x4bfffffd,0x804f0f54),0x804f0f4c)
        self.assertEqual(classify_and_target(0x48000003,0x804f0f54),0)
        self.assertIsNone(classify_and_target(0x4e800421,0x804f0f54))
        self.assertIsNone(classify_and_target(0x48000008,0x804f0f54))
    def test_native_cpp_trial_predicate_compiles_werror(self):
        compiler=shutil.which('g++')
        if compiler is None:self.skipTest('g++ unavailable')
        s=patch(self.prior)
        a=s.index('const bool v401_completed=')
        b=s.index('std::cout<<"V401_NAND_CALLSITE_TRIAL',a)
        fixture=('#include <cstdint>\n'
                 'namespace nwii {namespace runtime {\n'
                 'unsigned v401_reported=1u,v401_kind=1u,'
                 'v401_mapped=1u,v401_direct_match=1u;\n'
                 '}}\nint main(){const bool v400_completed=true;\n'
                 +s[a:b]+'\nreturn int(v401_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'fixture.cpp'
            path.write_text(fixture,encoding='utf-8')
            result=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                '-Werror','-Wno-unused-variable','-fsyntax-only',str(path)],
                text=True,capture_output=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr[-2000:])
    def test_fail_closed_source_seams(self):
        for altered in (
            self.prior.replace(STATE,'gone',1),
            self.prior.replace(RESET,'gone',1),
            self.prior.replace(WORD,'gone',1),
            self.prior.replace(STOP,'gone',1),
            self.prior.replace(TRIAL,'gone',1),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(altered)
if __name__=='__main__':unittest.main()
