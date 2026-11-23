#!/usr/bin/env python3
"""V408 original-free 50-call private-harness derivation and C++ checks."""
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v404_nand_extended import Tests as F404
from derive_v404_nand_extended import patch as v404
from derive_v408_nand_cut50 import patch,CAP_SEAMS,MARKERS

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        F404.setUpClass()
        cls.prior=v404(F404.prior)
    def test_original_guest_route_kept_and_exact_call_50_stop(self):
        source=self.prior
        out=patch(source)
        self.assertIn('if(owned||v396_calls==50u){',out)
        self.assertIn('const bool bounded=!owned&&v396_calls==50u;',out)
        self.assertIn('nwii::runtime::v396_calls==50u',out)
        self.assertIn('nwii::runtime::v396_calls<=50u',out)
        self.assertIn('V408_NAND_CUT50_STOP calls=',out)
        self.assertIn('V408_NAND_CUT50_TRIAL calls=',out)
        self.assertNotIn('if(owned||v396_calls==96u){',out)
        self.assertIn('if(owned||v396_calls==96u){',source)
        self.assertEqual(out.count('v408_completed'),3)
        self.assertEqual(out.count('try{run_game(c);}'),source.count('try{run_game(c);}'))
        self.assertIn('V403_NAND_CALL_PROVENANCE ctr=',out)
        self.assertIn('V389_NAND_FLAG_ACK before=',out)
        for illegal in ('ctx.pc=', 'ctx.lr=', 'ctx.ctr=',
                        'ctx.gpr[3]=','ipc70_bus.write32(',
                        'ipc70_bus.tick(','service_one('):
            self.assertNotIn(illegal,' '.join(MARKERS.values())+
                             ' '.join(n for n,count in CAP_SEAMS.values()))
    def test_stop_verification_compiles_cpp20(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('g++ not available')
        s=patch(self.prior)
        first=s.index('const bool v408_completed=')
        end=s.index('std::cout<<"V408_NAND_CUT50_TRIAL',first)
        cpp=(
            '#include <cstdint>\nnamespace nwii{namespace runtime{\n'
            'unsigned v396_kind=2u,v396_calls=50u,'
            'v398_site_seen=1u,v400_parent_site=1u;\n'
            '}}\nint main(){const bool v401_completed=true;\n'
            +s[first:end]+'\nreturn int(v408_completed);}\n'
        )
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.cpp'
            p.write_text(cpp,encoding='utf-8')
            res=subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror',
                   '-Wno-unused-variable','-fsyntax-only',str(p)],
                   capture_output=True,text=True,check=False)
            self.assertEqual(res.returncode,0,res.stderr[-1800:])
    def test_changed_seams_and_duplicate_application_rejected(self):
        for seam in (*CAP_SEAMS.keys(),*MARKERS.keys(),'v404_completed',
                     'V403_NAND_CALL_PROVENANCE ctr='):
            with self.subTest(seam=seam):
                with self.assertRaises(ValueError):
                    patch(self.prior.replace(seam,'missing',1))
        with self.assertRaises(ValueError):patch(patch(self.prior))
if __name__=='__main__':unittest.main()
