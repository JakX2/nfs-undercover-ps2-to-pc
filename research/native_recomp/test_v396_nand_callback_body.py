#!/usr/bin/env python3
"""V396 source originality, selected callback provenance and safety tests."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v395_nand_isfs_next import Tests as Fixture395
from derive_v395_nand_isfs_next import patch as v395
from derive_v396_nand_callback_body import patch,TRACE,STOP,CONTINUE,MARKER,TRIAL
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture395.setUpClass()
        cls.prior=v395(Fixture395.prior)
    def test_guest_selected_callback_only_and_prior_ack_proofs(self):
        s=patch(self.prior)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL),1)
        self.assertIn(CONTINUE,s)
        self.assertNotIn(STOP,s)
        self.assertIn('if(mapped&&selected&&userdata){',s)
        self.assertIn('return; // actual guest-selected callback body',s)
        self.assertIn('V395_NAND_ISFS_NEXT guest=',s)
        self.assertIn('V389_NAND_FLAG_ACK before=',s)
        self.assertIn('check(v395_completed,',s)
        self.assertIn('check(v396_completed,',s)
        self.assertIn('check(guest,',s)
        self.assertIn('const bool verified=guest&&(owned||bounded);',s)
        self.assertNotIn('check(clear&&masked&&registered&&guest',s)
        self.assertEqual(s.count('nwii::runtime::v396_kind=0u;'),1)
        self.assertLess(s.index('nwii::runtime::v396_kind=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
    def test_callback_target_classified_not_hardcoded(self):
        for token in (
            'v394_isfs_seen==1u&&v395_next_seen==1u',
            'ctx.inst_count>v396_start_inst',
            'ctx.lr>=v395_next_pc&&',
            'ctx.lr-v395_next_pc<0x800u',
            '((*ctl&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)==0u)',
            '!ipc70_bus.external_irq_level()',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'addr==0x8051e06cu',
            'v396_calls==24u',
            '<<" masked="<<unsigned(masked)',
            '<<" registered="<<unsigned(registered)',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(token,TRACE,token)
        for forbidden in ('service_one(', 'ipc70_bus.write32(', 'ipc70_bus.tick(',
                          'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=',
                          'ctx.gpr[3]=', 'StmIos::Reply','StmIos::Invalid'):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:self.assertNotIn(forbidden,TRACE)
    def test_original_guest_completion_predicates_compile_werror(self):
        compiler=shutil.which('g++')
        if compiler is None:self.skipTest('g++ is unavailable')
        source=patch(self.prior)
        blocks=[]
        for name,finish in (
            ('const bool v390_completed=', 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
            ('const bool v391_completed=', 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
            ('const bool v392_completed=', 'std::cout<<"V392_NAND_POST_CACHE_TRIAL'),
            ('const bool v393_completed=', 'std::cout<<"V393_NAND_NEXT_TRIAL'),
            ('const bool v394_completed=', 'std::cout<<"V394_NAND_ISFS_TRIAL'),
            ('const bool v395_completed=', 'std::cout<<"V395_NAND_ISFS_TRIAL'),
            ('const bool v396_completed=', 'std::cout<<"V396_NAND_CB_TRIAL'),
        ):
            i=source.index(name);j=source.index(finish,i)
            blocks.append(source[i:j])
        fixture=(
            '#include <cstdint>\n'
            'struct Context{uint32_t pc=0u,lr=0u;bool is_running=false;};\n'
            'namespace nwii{namespace runtime{\n'
            'uint32_t v390_call_seen=0u,v390_call_pc=0u,v390_call_lr=0u;\n'
            'uint32_t v391_kind=0u,v391_calls=0u,v391_next_pc=0u,v391_next_lr=0u;\n'
            'uint32_t v392_kind=0u,v392_calls=0u,v392_next_pc=0u,v392_next_lr=0u;\n'
            'uint32_t v393_next_seen=0u,v393_next_pc=0u,v393_next_lr=0u;\n'
            'uint32_t v394_context_seen=0u,v394_isfs_seen=0u;\n'
            'uint32_t v395_next_seen=0u,v395_next_pc=0u,v395_next_lr=0u;\n'
            'uint32_t v396_kind=0u,v396_calls=0u,v396_stop_pc=0u,v396_stop_lr=0u;\n'
            '}}\n'
            'int main(){Context c{};const bool v389_completed=true;\n'
            +'\n'.join(blocks)+'\nreturn int(v396_completed);}\n'
        )
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'original_free_v396.cpp'
            file.write_text(fixture,encoding='utf-8')
            result=subprocess.run(
                [compiler,'-std=c++20','-Wall','-Wextra','-Werror',
                 '-Wno-unused-variable','-fsyntax-only',str(file)],
                capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr[-1600:])
    def test_prior_guest_observer_drift_detected(self):
        for changed in (
            self.prior.replace('V395_NAND_ISFS_NEXT guest=','lost'),
            self.prior.replace('V394_NAND_ISFS_ENTRY guest=','lost'),
            self.prior.replace('V389_NAND_FLAG_ACK before=','lost'),
            self.prior.replace(STOP,'lost'),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(changed)
if __name__=="__main__":unittest.main()
