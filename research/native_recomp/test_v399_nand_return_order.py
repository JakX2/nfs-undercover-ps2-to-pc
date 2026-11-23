#!/usr/bin/env python3
"""V399 read-only original guest callback-continuation source checks."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v398_nand_return_site import Tests as Fixture398
from derive_v398_nand_return_site import patch as v398
from derive_v399_nand_resume_chain import (
    patch,STATE,RESET,CALLSITE,LATER,STOP,TRIAL,CALLSITE_NEXT,
    LATER_NEXT,STOP_NEXT,ENTRY,TRIAL_MARKER)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture398.setUpClass()
        cls.prior=v398(Fixture398.prior)
    def test_guest_read_only_opcode_and_temporal_classification(self):
        s=patch(self.prior)
        self.assertEqual(s.count(ENTRY),1)
        self.assertEqual(s.count(TRIAL_MARKER),1)
        self.assertIn('const uint32_t v399_call=ctx.mmu.read32(ctx.pc-4u)',CALLSITE_NEXT)
        self.assertIn('((v399_call>>1)&1023u)==528u',CALLSITE_NEXT)
        self.assertIn('v398_site_seen==1u&&v398_site_mapped==1u',LATER_NEXT)
        self.assertIn('if(v397_isfs)v399_isfs_after=1u;',LATER_NEXT)
        self.assertIn('if(v397_parent)v399_parent_after=1u;',LATER_NEXT)
        self.assertIn('blr_verified=0',STOP_NEXT)
        self.assertIn('V398_NAND_RETURN_PC samples=',s)
        self.assertIn('if(owned||v396_calls==24u)',s)
        self.assertLess(s.index('nwii::runtime::v399_isfs_after=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
        for forbidden in ('ctx.pc=', 'ctx.lr=', 'ctx.msr=', 'ctx.gpr[3]=',
                          'ctx.mmu.write','service_one(','ipc70_bus.write32('):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(
                    r'\b'+re.escape(forbidden)+r'(?!=)',CALLSITE_NEXT+LATER_NEXT))
            else:
                self.assertNotIn(forbidden,CALLSITE_NEXT+LATER_NEXT)
    def test_powerpc_indirect_link_opcode_classifier(self):
        def bctrl(word:int)->bool:
            return (word>>26)==19 and ((word>>1)&1023)==528 and (word&1)==1
        self.assertTrue(bctrl(0x4e800421))
        for instruction in (0x4e800420,0x4e800020,0x4e800021,0,0xffffffff):
            self.assertFalse(bctrl(instruction))
    def test_trial_predicate_compiles_werror(self):
        cc=shutil.which('g++')
        if cc is None:self.skipTest('g++ missing')
        s=patch(self.prior)
        begin=s.index('const bool v399_completed=')
        end=s.index('std::cout<<"V399_NAND_RETURN_TRIAL',begin)
        text=('#include <cstdint>\n'
              'namespace nwii{namespace runtime{\n'
              'unsigned v399_reported=1u,v399_bctrl=1u,'
              'v399_isfs_after=1u,v399_parent_after=0u;\n'
              'unsigned v398_site_seen=1u,v398_site_mapped=1u;\n'
              '}}\nint main(){const bool v398_completed=true;\n'+
              s[begin:end]+'\nreturn int(v399_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'predicate.cpp'
            p.write_text(text,encoding='utf-8')
            result=subprocess.run([cc,'-std=c++20','-Wall','-Wextra',
                   '-Werror','-Wno-unused-variable','-fsyntax-only',str(p)],
                   capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr[-1600:])
    def test_changed_or_duplicate_source_seams_fail_closed(self):
        for broken in (
            self.prior.replace(STATE,'missing',1),
            self.prior.replace(RESET,'missing',1),
            self.prior.replace(CALLSITE,'missing',1),
            self.prior.replace(LATER,'missing',1),
            self.prior.replace(STOP,'missing',1),
            self.prior.replace(TRIAL,'missing',1),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(broken)
if __name__=='__main__':unittest.main()
