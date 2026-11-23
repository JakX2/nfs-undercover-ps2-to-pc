#!/usr/bin/env python3
"""V393 source seam, PowerPC guest/callback safety and C++ compilation."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v392_nand_post_cache import Tests as Fixture392
from derive_v392_nand_post_cache import patch as v392
from derive_v393_nand_guest_next import patch,TRACE,STOP,CONTINUE,MARKER,TRIAL

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture392.setUpClass()
        cls.prior=v392(Fixture392.prior)
    def test_only_first_authentic_non_cache_callee_can_continue(self):
        result=patch(self.prior)
        self.assertEqual(result.count(MARKER),1)
        self.assertEqual(result.count(TRIAL),1)
        self.assertNotIn(STOP,result)
        self.assertIn(CONTINUE,result)
        self.assertIn('if(v392_kind==1u){',result)
        self.assertIn('v393_start_inst=ctx.inst_count;',result)
        self.assertIn('V392_NAND_POST_CACHE_EVENT kind=',result)
        self.assertIn('V391_NAND_POST_ACK_EVENT kind=',result)
        self.assertIn('V389_NAND_FLAG_ACK before=',result)
        self.assertIn('check(v393_completed,',result)
        self.assertEqual(result.count('nwii::runtime::v393_next_seen=0u;'),1)
        self.assertLess(result.index('nwii::runtime::v393_next_seen=0u;'),
                        result.index('c.is_running=true; // execute up to 16'))
    def test_guest_interrupt_no_fabricated_context_or_callback(self):
        for token in (
            'v392_kind==1u&&v393_next_seen==0u',
            'v392_next_pc!=0x80522294u',
            'ctx.inst_count>v393_start_inst',
            '((*ctrl&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)==0u)',
            '!ipc70_bus.external_irq_level()',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'addr==0x80522af4u',
            'addr==0x805228ccu',
            'addr==0x804f0e04u',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):
            self.assertIn(token,TRACE,token)
        for forbidden in ('service_one(','ipc70_bus.write32(', 'ipc70_bus.tick(',
                          'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=',
                          'ctx.gpr[3]=', 'StmIos::Reply', 'StmIos::Invalid'):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:self.assertNotIn(forbidden,TRACE)
    def test_earlier_result_predicates_compile_werror(self):
        compiler=shutil.which('g++')
        if compiler is None:self.skipTest('g++ not available')
        s=patch(self.prior)
        blocks=[]
        for name,next_name in (
            ('const bool v390_completed=', 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
            ('const bool v391_completed=', 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
            ('const bool v392_completed=', 'std::cout<<"V392_NAND_POST_CACHE_TRIAL'),
        ):
            start=s.index(name)
            end=s.index(next_name,start)
            blocks.append(s[start:end])
        snippet=(
            '#include <cstdint>\n'
            'struct Context {uint32_t pc=0u,lr=0u;};\n'
            'namespace nwii{namespace runtime{\n'
            'uint32_t v390_call_seen=0u,v390_call_pc=0u,v390_call_lr=0u;\n'
            'uint32_t v391_kind=0u,v391_calls=0u,v391_next_pc=0u,v391_next_lr=0u;\n'
            'uint32_t v392_kind=0u,v392_calls=0u,v392_next_pc=0u,v392_next_lr=0u;\n'
            'uint32_t v393_next_seen=0u,v393_next_pc=0u,v393_next_lr=0u;\n'
            '}}\n'
            'int main(){Context c{};const bool v389_completed=true;\n'
            +'\n'.join(blocks)+
            '\nreturn int(v392_completed);}\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'free.cpp'
            source.write_text(snippet,encoding='utf-8')
            res=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                 '-Werror','-Wno-unused-variable','-fsyntax-only',str(source)],
                 capture_output=True,text=True,check=False)
            self.assertEqual(res.returncode,0,res.stderr[-1600:])
    def test_missing_authentic_prior_observer_fails_closed(self):
        for changed in (
            self.prior.replace('V392_NAND_POST_CACHE_EVENT kind=','absent'),
            self.prior.replace('V392_NAND_POST_CACHE_TRIAL kind=','absent'),
            self.prior.replace('V390_NAND_POST_ACK guest=','absent'),
            self.prior.replace('V389_NAND_FLAG_ACK before=','absent'),
            self.prior.replace(STOP,'absent'),
            patch(self.prior),
        ):
            with self.assertRaises(ValueError):patch(changed)
if __name__=="__main__":unittest.main()
