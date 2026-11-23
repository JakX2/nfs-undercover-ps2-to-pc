#!/usr/bin/env python3
"""V397 synthetic-only transformation, provenance and -Werror regression."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v396_nand_callback_body import Tests as Fixture396
from derive_v396_nand_callback_body import patch as v396
from derive_v397_nand_callback_lineage import (
    patch,STATE,RESET,COUNT,COUNT_NEW,STOP,STOP_NEW,MARKER,TRIAL)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture396.setUpClass()
        cls.prior=v396(Fixture396.prior)
    def test_observer_read_only_and_bounded(self):
        s=patch(self.prior)
        self.assertIn(COUNT_NEW,s)
        self.assertIn(STOP_NEW,s)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL),1)
        self.assertLess(s.index('nwii::runtime::v397_origin_mask=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
        for token in ('ctx.lr>=v395_next_pc&&','ctx.lr>=0x804f0e04u&&',
                      'ctx.lr>=0x805192acu&&','ctx.lr==v395_next_lr',
                      '++v396_calls;','if(owned||v396_calls==24u)'):
            self.assertIn(token,COUNT_NEW)
        for forbidden in ('ipc70_bus.write32(', 'ipc70_bus.tick(', 'service_one(',
                          'ctx.msr=', 'ctx.pc=', 'ctx.gpr[3]=',
                          'ctx.mmu.write','StmIos::Reply'):
            self.assertNotIn(forbidden,COUNT_NEW+STOP_NEW)
        # Equality (ctx.lr==...) is read-only; reject only assignments.
        self.assertIsNone(re.search(r'\bctx\.lr\s*=(?!=)',COUNT_NEW+STOP_NEW))
        self.assertIn('V396_NAND_CB_BODY kind=',s)
        self.assertIn('V395_NAND_ISFS_NEXT guest=',s)
        self.assertIn('V389_NAND_FLAG_ACK before=',s)
    def test_trial_predicate_compiles_werror(self):
        compiler=shutil.which('g++')
        if not compiler:self.skipTest('g++ unavailable')
        s=patch(self.prior)
        start=s.index('const bool v397_completed=')
        end=s.index('std::cout<<"V397_NAND_ORIGINS_TRIAL',start)
        source=('#include <cstdint>\n'
                'namespace nwii{namespace runtime{\n'
                'uint32_t v397_origin_mask=1u,v397_last_origin=1u,v396_calls=24u;\n'
                '}}\nint main(){const bool v396_completed=true;\n'+
                s[start:end]+'\nreturn int(v397_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.cpp'
            p.write_text(source,encoding='utf-8')
            r=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                '-Werror','-Wno-unused-variable','-fsyntax-only',str(p)],
                text=True,capture_output=True,check=False)
            self.assertEqual(r.returncode,0,r.stderr[-1800:])
    def test_missing_or_duplicate_seams_fail_closed(self):
        for broken in (
            self.prior.replace(STATE,'gone',1),
            self.prior.replace(RESET,'gone',1),
            self.prior.replace(COUNT,'gone',1),
            self.prior.replace(STOP,'gone',1),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(broken)
if __name__=="__main__":unittest.main()
