#!/usr/bin/env python3
"""V405 source-only read-only guest 49–96 origin classifier checks."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v404_nand_extended import Tests as Fixture404
from derive_v404_nand_extended import patch as v404
from derive_v405_nand_second_half import (
    patch,STATE,RESET,TRACE,STOP,TRIAL,TRACE_NEXT,STOP_NEXT,
    TRIAL_NEXT,MARKER,TRIAL_MARKER,EXIT_CHECK)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture404.setUpClass()
        cls.prior=v404(Fixture404.prior)
    def test_guest_state_is_preserved_and_second_half_bounded(self):
        code=patch(self.prior)
        self.assertEqual(code.count(MARKER),1)
        self.assertEqual(code.count(TRIAL_MARKER),1)
        self.assertEqual(code.count('V406_NAND_CHECKPOINT call='),1)
        self.assertEqual(code.count('V410_NAND_GUEST_RUN_EXIT calls='),1)
        self.assertIn('check(v390_completed,',code)
        self.assertIn('v410_matched_stop',code)
        self.assertLess(code.index('V410_NAND_GUEST_RUN_EXIT calls='),
                        code.index('V390 original NAND guest never left Hollywood ACK'))
        self.assertIn('if(v406_checkpoint_count<48u)',TRACE_NEXT)
        self.assertIn('std::cout<<"V406_NAND_CHECKPOINT call="',TRACE_NEXT)
        self.assertIn('if(v396_calls>48u&&v396_calls<=96u)',TRACE_NEXT)
        self.assertIn('if(v397_class==1u)++v405_selected;',TRACE_NEXT)
        self.assertIn('else if(v397_class==2u)++v405_isfs;',TRACE_NEXT)
        self.assertIn('else if(v397_class==3u)++v405_parent;',TRACE_NEXT)
        self.assertIn('if(addr==0x8051e06cu)++v405_nand;',TRACE_NEXT)
        self.assertIn('if(addr==0x80522294u)++v405_cache;',TRACE_NEXT)
        self.assertIn('if(owned||v396_calls==96u){',code)
        self.assertIn('V404_NAND_EXTENDED_STOP calls=',code)
        self.assertIn('V403_NAND_CALL_PROVENANCE ctr=',code)
        self.assertIn('blr_verified=0',code)
        self.assertLess(code.index('nwii::runtime::v405_tail_calls=0u;'),
                        code.index('c.is_running=true; // execute up to 16'))
        for forbid in ('ctx.pc=', 'ctx.lr=', 'ctx.ctr=', 'ctx.gpr[1]=',
                       'ctx.mmu.write','ipc70_bus.write32(', 'service_one('):
            if forbid.endswith('='):
                self.assertIsNone(re.search(
                    r'\b'+re.escape(forbid)+r'(?!=)',TRACE_NEXT+STOP_NEXT+TRIAL_NEXT))
            else:
                self.assertNotIn(forbid,TRACE_NEXT+STOP_NEXT+TRIAL_NEXT)
    def test_guest_counters_and_proof_compile_and_run(self):
        cc=shutil.which('g++')
        if cc is None:self.skipTest('g++ unavailable')
        fragment=TRACE_NEXT[len(TRACE):]
        proof=TRIAL_NEXT[TRIAL_NEXT.index('const unsigned v405_expected='):
                         TRIAL_NEXT.index('std::cout<<"V405_NAND_SECOND_TRIAL')]
        cpp=(
            '#include <cstdint>\n#include <iostream>\n'
            'namespace nwii{namespace runtime{\n'
            'unsigned v396_calls=48u,v405_tail_calls=0u,'
            'v405_selected=0u,v405_isfs=0u,v405_parent=0u,'
            'v405_other=0u,v405_nand=0u,v405_cache=0u,'
            'v405_reported=1u,v406_checkpoint_count=0u,'
            'v398_site_seen=1u,v400_parent_site=1u;\n'
            '}}\n'
            'static void observe(unsigned call_class,uint32_t addr){\n'
            'using namespace nwii::runtime;\n'
            'unsigned v397_class=call_class;\n'
            'uint32_t v396_calls=++nwii::runtime::v396_calls;\n'
            +fragment+'\n}\n'
            'int main(){\n'
            'for(unsigned i=0u;i<48u;++i)observe(i%4u+1u,0x80519318u);\n'
            'using namespace nwii::runtime;\n'
            'const bool v404_completed=true;\n'
            +proof+'\n'
            'if(!v405_completed||v405_tail_calls!=48u||'
            'v405_selected!=12u||v405_isfs!=12u||'
            'v405_parent!=12u||v405_other!=12u)return 1;\n'
            'return 0;}\n'
        )
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'fixture.cpp'
            exe=Path(td)/'fixture'
            path.write_text(cpp,encoding='utf-8')
            build=subprocess.run([cc,'-std=c++20','-O1','-Wall','-Wextra',
               '-Werror',str(path),'-o',str(exe)],capture_output=True,
               text=True,check=False)
            self.assertEqual(build.returncode,0,build.stderr[-2200:])
            result=subprocess.run([str(exe)],capture_output=True,
                text=True,check=False,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr[-1000:])
    def test_source_seams_fail_closed(self):
        for needle in (STATE,RESET,TRACE,STOP,TRIAL,EXIT_CHECK):
            with self.subTest(needle=needle[:20]):
                with self.assertRaises(ValueError):
                    patch(self.prior.replace(needle,'missing',1))
        # The new V405 marker does not exist in the V404 input; injecting
        # a pre-existing marker must fail, not deleting a missing one.
        with self.assertRaises(ValueError):patch(self.prior+"\n"+MARKER)
        with self.assertRaises(ValueError):
            patch(self.prior+"\nV406_NAND_CHECKPOINT call=")
        with self.assertRaises(ValueError):patch(patch(self.prior))
if __name__=='__main__':
    unittest.main()
