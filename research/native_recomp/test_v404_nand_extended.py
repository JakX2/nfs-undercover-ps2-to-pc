#!/usr/bin/env python3
"""V404 independent 96-call derivation, no original game assets."""
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v403_nand_call_provenance import Tests as Fixture403
from derive_v403_nand_call_provenance import patch as v403
from derive_v402_long_frontier import patch as v402
from derive_v404_nand_extended import patch,CAP_SEAMS,MARKERS

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture403.setUpClass()
        baseline=v403(Fixture403.prior)
        if 'try{run_game(c);}' not in baseline:
            baseline+='\ntry{run_game(c);}\n'
        cls.prior=v402(baseline)
    def test_48_baseline_is_not_modified_and_96_is_real(self):
        previous=self.prior
        out=patch(previous)
        self.assertIn('if(owned||v396_calls==96u){',out)
        self.assertIn('const bool bounded=!owned&&v396_calls==96u;',out)
        self.assertIn('nwii::runtime::v396_calls==96u',out)
        self.assertIn('nwii::runtime::v396_calls<=96u',out)
        self.assertNotIn('if(owned||v396_calls==48u){',out)
        self.assertIn('if(owned||v396_calls==48u){',previous)
        self.assertIn('V404_NAND_EXTENDED_STOP calls=',out)
        self.assertIn('V404_NAND_EXTENDED_TRIAL calls=',out)
        self.assertEqual(out.count('v404_completed'),3)
        self.assertIn('V403_NAND_CALL_PROVENANCE ctr=',out)
        self.assertIn('V401_NAND_CALLSITE mapped=',out)
        self.assertIn('V389_NAND_FLAG_ACK before=',out)
        self.assertEqual(out.count('try{run_game(c);}'),
                         previous.count('try{run_game(c);}'))
        for forbidden in ('ctx.pc=', 'ctx.lr=', 'ctx.ctr=',
                          'ctx.gpr[1]=','ctx.mmu.write32(',
                          'ipc70_bus.write32(', 'ipc70_bus.tick(', 'service_one('):
            self.assertNotIn(forbidden,' '.join(MARKERS.values())+
                             ' '.join(n for n,k in CAP_SEAMS.values()))
    def test_v404_native_stop_proof_compiles(self):
        compiler=shutil.which('g++')
        if compiler is None:self.skipTest('g++ unavailable')
        s=patch(self.prior)
        begin=s.index('const bool v404_completed=')
        end=s.index('std::cout<<"V404_NAND_EXTENDED_TRIAL',begin)
        proof=('#include <cstdint>\n'
               'namespace nwii{namespace runtime{\n'
               'unsigned v396_kind=2u,v396_calls=96u,'
               'v398_site_seen=1u,v400_parent_site=1u;\n'
               '}}\nint main(){const bool v401_completed=true;\n'
               +s[begin:end]+'\nreturn int(v404_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'v404.cpp'
            p.write_text(proof,encoding='utf-8')
            result=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                '-Werror','-Wno-unused-variable','-fsyntax-only',str(p)],
                capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr[-1400:])
    def test_duplicate_or_changed_anchor_fails_closed(self):
        for seam in (*CAP_SEAMS.keys(),*MARKERS.keys(),'v402_completed',
                     'V403_NAND_CALL_PROVENANCE ctr='):
            altered=self.prior.replace(seam,'missing',1)
            with self.subTest(seam=seam):
                with self.assertRaises(ValueError):patch(altered)
        with self.assertRaises(ValueError):patch(patch(self.prior))
if __name__=='__main__':
    unittest.main()
