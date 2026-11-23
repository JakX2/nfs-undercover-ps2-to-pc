#!/usr/bin/env python3
"""V400 synthetic guest parent return site and opcode source guards."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v399_nand_return_order import Tests as Fixture399
from derive_v399_nand_resume_chain import patch as v399
from derive_v400_nand_parent_resume import (
    patch,STATE,RESET,PENDING,LATER,STOP,TRIAL,HOOK,LATER_NEXT,
    STOP_NEXT,MARKER,TRIAL_MARKER)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture399.setUpClass()
        cls.prior=v399(Fixture399.prior)
    def test_parent_guest_lr_read_only_and_ordered(self):
        s=patch(self.prior)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL_MARKER),1)
        self.assertIn('ctx.pc==0x805192acu',HOOK)
        self.assertIn('ctx.mmu.read32(0x805192a8u)',HOOK)
        self.assertIn('v398_site_seen==1u&&v398_site_mapped==1u',HOOK)
        self.assertIn('if(v400_parent_site==1u',LATER_NEXT)
        self.assertIn('v400_parent_after==1u',STOP_NEXT)
        self.assertIn('V399_NAND_RETURN_ORDER site=',s)
        self.assertIn('V398_NAND_RETURN_PC samples=',s)
        self.assertIn('if(owned||v396_calls==24u)',s)
        self.assertLess(s.index('nwii::runtime::v400_parent_site=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
        for forbidden in ('ctx.pc=', 'ctx.lr=', 'ctx.msr=', 'ctx.gpr[3]=',
                          'ctx.mmu.write', 'service_one(', 'ipc70_bus.write32('):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(
                    r'\b'+re.escape(forbidden)+r'(?!=)',HOOK+LATER_NEXT))
            else:
                self.assertNotIn(forbidden,HOOK+LATER_NEXT)
    def test_powerpc_original_caller_link_opcode_classification(self):
        def link_opcode(word):
            return ((word>>26)==18 and (word&1)==1) or (
                (word>>26)==19 and ((word>>1)&1023)==528 and (word&1)==1)
        self.assertTrue(link_opcode(0x48000001))
        self.assertTrue(link_opcode(0x4e800421))
        for bad in (0,0x48000000,0x4e800420,0x4e800020,0xffffffff):
            self.assertFalse(link_opcode(bad))
    def test_v400_trial_proof_compiles_werror(self):
        compiler=shutil.which('g++')
        if not compiler:self.skipTest('g++ unavailable')
        s=patch(self.prior)
        a=s.index('const bool v400_completed=')
        b=s.index('std::cout<<"V400_NAND_PARENT_TRIAL',a)
        text=('#include <cstdint>\n'
              'namespace nwii{namespace runtime{\n'
              'unsigned v400_reported=1u,v400_parent_site=1u,'
              'v400_parent_mapped=1u,v400_link=1u,v400_selected_first=1u,'
              'v400_parent_after=1u;\n'
              '}}\nint main(){const bool v399_completed=true;\n'+
              s[a:b]+'\nreturn int(v400_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.cpp'
            p.write_text(text,encoding='utf-8')
            r=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                '-Werror','-Wno-unused-variable','-fsyntax-only',str(p)],
                capture_output=True,text=True,check=False)
            self.assertEqual(r.returncode,0,r.stderr[-1500:])
    def test_missing_original_source_seams_fail_closed(self):
        for altered in (
            self.prior.replace(STATE,'missing',1),
            self.prior.replace(RESET,'missing',1),
            self.prior.replace(PENDING,'missing',1),
            self.prior.replace(LATER,'missing',1),
            self.prior.replace(STOP,'missing',1),
            self.prior.replace(TRIAL,'missing',1),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(altered)
if __name__=="__main__":unittest.main()
