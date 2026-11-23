#!/usr/bin/env python3
"""V403 original-free AOT provenance source and PPC opcode family tests."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v401_nand_linksite_classify import Tests as Fixture401
from derive_v401_nand_linksite_classify import patch as v401
from derive_v403_nand_call_provenance import (
    patch,STATE,RESET,ENTRY_SAVE,RESUME,OPCODE,STOP,TRIAL,
    ENTRY_NEW,RESUME_NEW,OPCODE_NEW,STOP_NEW,MARKER,TRIAL_MARKER)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture401.setUpClass()
        cls.prior=v401(Fixture401.prior)
    def test_only_native_guest_observation_no_register_or_memory_writes(self):
        s=patch(self.prior)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL_MARKER),1)
        self.assertIn('ctx.ctr==addr',ENTRY_NEW)
        self.assertIn('v403_selected_sp=ctx.gpr[1]',ENTRY_NEW)
        self.assertIn('if(ctx.lr==ctx.pc)',RESUME_NEW)
        self.assertIn('if(ctx.gpr[1]==v403_selected_sp)',RESUME_NEW)
        self.assertIn('v401_op==19u&&v401_xo==528u',OPCODE_NEW)
        self.assertIn('v399_call==0x60000000u',OPCODE_NEW)
        self.assertIn('blr_verified=0',STOP_NEW)
        self.assertIn('if(owned||v396_calls==24u)',s)
        self.assertIn('V401_NAND_CALLSITE mapped=',s)
        self.assertIn('V389_NAND_FLAG_ACK before=',s)
        self.assertLess(s.index('nwii::runtime::v403_target_ctr=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
        for bad in ('ctx.pc=', 'ctx.lr=', 'ctx.ctr=', 'ctx.gpr[1]=',
                    'ctx.mmu.write','ipc70_bus.write32(','service_one('):
            if bad.endswith('='):
                self.assertIsNone(re.search(
                    r'\b'+re.escape(bad)+r'(?!=)',ENTRY_NEW+RESUME_NEW+OPCODE_NEW))
            else:self.assertNotIn(bad,ENTRY_NEW+RESUME_NEW+OPCODE_NEW)
    def test_source_passes_cpp_werror_and_family_classification(self):
        cc=shutil.which('g++')
        if cc is None:self.skipTest('g++ unavailable')
        block=OPCODE_NEW.split('        if(v401_kind==1u||v401_kind==2u){')[0]
        fixture=(
            '#include <cstdint>\n'
            'static unsigned classify(uint32_t word){\n'
            'const uint32_t v399_call=word;\n'
            'const uint32_t v401_op=v399_call>>26;\n'
            'const uint32_t v401_xo=(v399_call>>1)&1023u;\n'
            'unsigned v401_kind=5u,v403_family=0u;\n'
            +block+'\nreturn v403_family;}\n'
            'int main(){\n'
            'if(classify(0x48000000u)!=1u)return 1;\n'
            'if(classify(0x40000000u)!=2u)return 2;\n'
            'if(classify(0x4e800020u)!=3u)return 3;\n'
            'if(classify(0x4e800420u)!=4u)return 4;\n'
            'if(classify(0x60000000u)!=5u)return 5;\n'
            'if(classify(0x80000000u)!=6u)return 6;\n'
            'if(classify(0x7c0802a6u)!=7u)return 7;\n'
            'if(classify(0x38000000u)!=8u)return 8;\n'
            'return 0;}\n')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'classification.cpp'
            exe=Path(td)/'classification'
            path.write_text(fixture,encoding='utf-8')
            compiled=subprocess.run([cc,'-std=c++20','-O1','-Wall','-Wextra',
                '-Werror','-fsyntax-only',str(path)],
                capture_output=True,text=True,check=False)
            self.assertEqual(compiled.returncode,0,compiled.stderr[-1700:])
            built=subprocess.run([cc,'-std=c++20','-O1',str(path),'-o',str(exe)],
                capture_output=True,text=True,check=False)
            self.assertEqual(built.returncode,0,built.stderr[-1700:])
            execution=subprocess.run([str(exe)],capture_output=True,
                text=True,timeout=5,check=False)
            self.assertEqual(execution.returncode,0,execution.stderr[-1000:])
    def test_v403_werror_trial_predicate(self):
        cc=shutil.which('g++')
        if cc is None:self.skipTest('g++ unavailable')
        s=patch(self.prior)
        start=s.index('const bool v403_completed=')
        end=s.index('std::cout<<"V403_NAND_CALL_PROVENANCE_TRIAL',start)
        source=('#include <cstdint>\nnamespace nwii{namespace runtime{\n'
                'unsigned v403_reported=1,v403_target_ctr=1,'
                'v403_return_sp=1,v403_return_lr=0,v403_family=4,'
                'v401_kind=5;\n}}\n'
                'int main(){const bool v401_completed=true;\n'
                +s[start:end]+'\nreturn int(v403_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'trial.cpp'
            p.write_text(source,encoding='utf-8')
            result=subprocess.run([cc,'-std=c++20','-Wall','-Wextra',
                '-Werror','-Wno-unused-variable','-fsyntax-only',str(p)],
                capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr[-1300:])
    def test_missing_seams_and_double_application_fail_closed(self):
        for broken in (
            self.prior.replace(STATE,'gone',1),
            self.prior.replace(RESET,'gone',1),
            self.prior.replace(ENTRY_SAVE,'gone',1),
            self.prior.replace(RESUME,'gone',1),
            self.prior.replace(OPCODE,'gone',1),
            self.prior.replace(STOP,'gone',1),
            self.prior.replace(TRIAL,'gone',1),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(broken)
if __name__=='__main__':unittest.main()
