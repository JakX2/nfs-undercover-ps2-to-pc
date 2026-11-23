#!/usr/bin/env python3
"""V402 independent original-free second-horizon derivation tests."""
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v401_nand_linksite_classify import Tests as Fixture401
from derive_v401_nand_linksite_classify import patch as v401
from derive_v402_long_frontier import patch,SEAMS,STOP,STOP_NEW,TRIAL,TRIAL_NEW,MARKER,TRIAL_MARKER
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture401.setUpClass()
        cls.prior=v401(Fixture401.prior)
        # The real owner harness has one run_game call. Earlier synthetic
        # callback fixtures omit its wrapper; provide the guard's fixture
        # geometry rather than weakening the original-source patch.
        if "try{run_game(c);}" not in cls.prior:
            cls.prior += "\ntry{run_game(c);}\n"
        assert cls.prior.count("try{run_game(c);}") == 1
    def test_baseline_is_preserved_and_extended_callee_is_bounded(self):
        s=patch(self.prior)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL_MARKER),1)
        self.assertNotIn("if(owned||v396_calls==24u){",s)
        self.assertEqual(s.count("if(owned||v396_calls==48u){"),1)
        self.assertIn('const bool bounded=!owned&&v396_calls==48u;',s)
        self.assertIn('nwii::runtime::v396_calls==48u',s)
        self.assertIn('nwii::runtime::v396_calls<=48u',s)
        self.assertIn('if(v396_calls<24u)v398_pre_cap=1u;',s)
        self.assertIn('if(v396_calls<24u)v400_parent_pre_cap=1u;',s)
        self.assertIn('V401_NAND_CALLSITE mapped=',s)
        self.assertIn('V399_NAND_RETURN_ORDER site=',s)
        self.assertIn('V389_NAND_FLAG_ACK before=',s)
        self.assertIn('V370_NAND_FLAG_W1C n=',s)
        for needle in ('ctx.pc=', 'ctx.lr=', 'ctx.gpr[3]=', 'ctx.msr=',
                       'ipc70_bus.write32(', 'ipc70_bus.tick(', 'service_one('):
            self.assertNotIn(needle,STOP_NEW+TRIAL_NEW)
    def test_v402_trial_predicate_compiles_werror(self):
        cc=shutil.which('g++')
        if cc is None:self.skipTest('g++ unavailable')
        s=patch(self.prior)
        start=s.index('const bool v402_completed=')
        finish=s.index('std::cout<<"V402_NAND_LONG_TRIAL',start)
        fixture=('#include <cstdint>\n'
                 'namespace nwii{namespace runtime{\n'
                 'unsigned v396_kind=2u,v396_calls=48u,'
                 'v398_site_seen=1u,v400_parent_site=1u;\n'
                 '}}\nint main(){const bool v401_completed=true;\n'
                 +s[start:finish]+'\nreturn int(v402_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.cpp'
            p.write_text(fixture,encoding='utf-8')
            result=subprocess.run([cc,'-std=c++20','-Wall','-Wextra',
               '-Werror','-Wno-unused-variable','-fsyntax-only',str(p)],
               text=True,capture_output=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr[-1600:])
    def test_changed_24_call_proof_and_duplicate_application_fail_closed(self):
        self.assertEqual(len(SEAMS),4)
        for needle in (*SEAMS.keys(),STOP,TRIAL):
            altered=self.prior.replace(needle,'missing',1)
            with self.subTest(needle=needle):
                with self.assertRaises(ValueError):patch(altered)
        with self.assertRaises(ValueError):patch(patch(self.prior))
if __name__=="__main__":unittest.main()
