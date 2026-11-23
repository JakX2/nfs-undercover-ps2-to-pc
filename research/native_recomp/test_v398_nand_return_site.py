#!/usr/bin/env python3
"""V398 synthetic-only transformation and native C++ predicate compilation."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v397_nand_callback_lineage import Tests as Fixture397
from derive_v397_nand_callback_lineage import patch as v397
from derive_v398_nand_return_site import (
    patch,STATE,RESET,CALLBACK,PENDING_HOOK,STOP,STOP_ADD,TRIAL,ENTRY,TRIAL_MARKER)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture397.setUpClass()
        cls.prior=v397(Fixture397.prior)
        # Earlier synthetic fixtures only modeled trace_call and trial
        # completion. V398 additionally instruments the existing pending-
        # callback boundary, so supply that original-free source seam here.
        if CALLBACK not in cls.prior:
            cls.prior += "\n" + CALLBACK + "\n  return false;\n}\n"
        assert cls.prior.count(CALLBACK)==1
    def test_genuine_pc_observed_without_state_mutation_or_stop_change(self):
        code=patch(self.prior)
        self.assertEqual(code.count(ENTRY),1)
        self.assertEqual(code.count(TRIAL_MARKER),1)
        self.assertEqual(code.count(PENDING_HOOK),1)
        self.assertIn('ctx.pc==v395_next_lr',PENDING_HOOK)
        self.assertIn('ctx.inst_count>v396_start_inst',PENDING_HOOK)
        self.assertIn('if(v398_samples<64u)++v398_samples',PENDING_HOOK)
        self.assertIn('ctx.mmu.get_ptr(ctx.pc)',PENDING_HOOK)
        self.assertIn('blr_verified=0',STOP_ADD)
        self.assertIn('if(owned||v396_calls==24u)',code)
        self.assertIn('V396_NAND_CB_BODY kind=',code)
        self.assertIn('V397_NAND_ORIGINS mask=',code)
        self.assertIn('V389_NAND_FLAG_ACK before=',code)
        for forbidden in ('ctx.is_running=', 'ctx.pc=', 'ctx.lr=',
                          'ctx.gpr[3]=', 'ctx.msr=', 'ctx.mmu.write',
                          'service_one(', 'ipc70_bus.tick(', 'ipc70_bus.write32('):
            # Equality is not an assignment; guard direct single '='.
            if forbidden.endswith('='):
                self.assertIsNone(re.search(
                    r'\b'+re.escape(forbidden)+r'(?!=)',PENDING_HOOK))
            else:
                self.assertNotIn(forbidden,PENDING_HOOK)
        self.assertLess(code.index('nwii::runtime::v398_samples=0u;'),
                        code.index('c.is_running=true; // execute up to 16'))
    def test_trial_predicate_compiles_with_werror(self):
        cxx=shutil.which('g++')
        if not cxx:self.skipTest('g++ unavailable')
        s=patch(self.prior)
        start=s.index('const bool v398_completed=')
        end=s.index('std::cout<<"V398_NAND_RETURN_TRIAL',start)
        fixture=('#include <cstdint>\n'
                 'namespace nwii {namespace runtime {\n'
                 'unsigned v398_reported=1u,v398_samples=0u;\n'
                 'uint32_t v395_next_lr=0x804f0f54u;\n'
                 '}}\n'
                 'int main(){const bool v397_completed=true;\n'
                 +s[start:end]+'return int(v398_completed);}\n')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.cpp'
            p.write_text(fixture,encoding='utf-8')
            out=subprocess.run([cxx,'-std=c++20','-Wall','-Wextra',
                '-Werror','-Wno-unused-variable','-fsyntax-only',str(p)],
                capture_output=True,text=True,check=False)
            self.assertEqual(out.returncode,0,out.stderr[-1400:])
    def test_pending_hook_compiles_and_executes_without_guest_mutation(self):
        compiler=shutil.which('g++')
        if compiler is None:self.skipTest('g++ unavailable')
        fixture=(
            '#include <cstdint>\n'
            'struct Memory{uint32_t data=1u;void* get_ptr(uint32_t pc){'
            'return pc==0x804f0f54u?&data:nullptr;}};\n'
            'struct CPUContext{uint32_t pc=0x804f0f54u;'
            'uint64_t inst_count=101u;Memory mmu;};\n'
            'namespace nwii{namespace runtime{\n'
            'bool v250_candidate_mode=true;\n'
            'unsigned v250_nand_seen=1u,v394_isfs_seen=1u,'
            'v395_next_seen=1u,v396_kind=0u,v396_calls=3u;\n'
            'uint64_t v396_start_inst=100u;\n'
            'uint32_t v395_next_lr=0x804f0f54u;\n'
            'unsigned v398_samples=0u,v398_site_seen=0u,'
            'v398_site_mapped=0u,v398_pre_cap=0u;\n'
            +PENDING_HOOK+' return false;\n}\n}}\n'
            'int main(){CPUContext ctx{};'
            'uint32_t saved_pc=ctx.pc;'
            'nwii::runtime::process_pending_callbacks(ctx);'
            'if(ctx.pc!=saved_pc||ctx.inst_count!=101u||'
            'nwii::runtime::v398_samples!=1u||'
            'nwii::runtime::v398_site_seen!=1u||'
            'nwii::runtime::v398_site_mapped!=1u||'
            'nwii::runtime::v398_pre_cap!=1u)return 1;'
            'ctx.pc=0x80510000u;ctx.inst_count=102u;'
            'nwii::runtime::process_pending_callbacks(ctx);'
            'if(ctx.pc!=0x80510000u||nwii::runtime::v398_samples!=2u)return 2;'
            'return 0;}\n'
        )
        with tempfile.TemporaryDirectory() as td:
            cpp=Path(td)/'synthetic.cpp'
            exe=Path(td)/'synthetic'
            cpp.write_text(fixture,encoding='utf-8')
            build=subprocess.run([compiler,'-std=c++20','-O1','-Wall',
                 '-Wextra','-Werror','-pedantic',str(cpp),'-o',str(exe)],
                 capture_output=True,text=True,check=False)
            self.assertEqual(build.returncode,0,build.stderr[-1800:])
            executed=subprocess.run([str(exe)],capture_output=True,text=True,
                                    check=False,timeout=5)
            self.assertEqual(executed.returncode,0,executed.stderr[-1200:])

    def test_seam_changes_fail_closed(self):
        for altered in (
            self.prior.replace(STATE,'gone',1),
            self.prior.replace(RESET,'gone',1),
            self.prior.replace(CALLBACK,'gone',1),
            self.prior.replace(STOP,'gone',1),
            self.prior.replace(TRIAL,'gone',1),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(altered)
if __name__=='__main__':unittest.main()
