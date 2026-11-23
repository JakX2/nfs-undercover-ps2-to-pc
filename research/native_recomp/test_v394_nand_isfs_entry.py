#!/usr/bin/env python3
"""V394 original-free guest ISFS callback entry source and compiler tests."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v393_nand_guest_next import Tests as Fixture393
from derive_v393_nand_guest_next import patch as v393
from derive_v394_nand_isfs_entry import patch,TRACE,STOP,CONTINUE,MARKER,TRIAL

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture393.setUpClass()
        cls.prior=v393(Fixture393.prior)
    def test_guarded_context_setter_without_forced_callback(self):
        s=patch(self.prior)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL),1)
        self.assertIn(CONTINUE,s)
        self.assertNotIn(STOP,s)
        self.assertIn('addr==0x805228ccu&&ctx.lr==0x80519298u',s)
        self.assertIn('return; // execute original guest OSSetCurrentContext',s)
        self.assertIn('V393_NAND_NEXT_CALL guest=',s)
        self.assertIn('V392_NAND_POST_CACHE_EVENT kind=',s)
        self.assertIn('V389_NAND_FLAG_ACK before=',s)
        self.assertEqual(s.count('nwii::runtime::v394_isfs_seen=0u;'),1)
        self.assertLess(s.index('nwii::runtime::v394_isfs_seen=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
    def test_guest_abi_metadata_read_only(self):
        for token in (
            'addr==0x804f0e04u&&ctx.pc==addr&&ctx.lr==0x805192acu',
            'v394_context_seen==1u&&v394_isfs_seen==0u',
            '((*control&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)==0u)',
            '!ipc70_bus.external_irq_level()',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'ctx.gpr[31]', 'request<=0xffffffd8u',
            'ctx.mmu.get_ptr(request+39u)',
            'ctx.mmu.read32(request+32u)==addr',
            'ctx.gpr[3]==ctx.mmu.read32(request+4u)',
            'ctx.gpr[4]==ctx.mmu.read32(request+36u)',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):self.assertIn(token,TRACE,token)
        for forbidden in ('service_one(', 'ipc70_bus.write32(', 'ipc70_bus.tick(',
                          'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=',
                          'ctx.gpr[3]=', 'StmIos::Reply','StmIos::Invalid'):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:self.assertNotIn(forbidden,TRACE)
        self.assertNotIn('return; // execute original guest OSSetCurrentContext',TRACE)
    def test_completion_predicates_compile_gcc_werror(self):
        compiler=shutil.which('g++')
        if compiler is None:self.skipTest('g++ missing')
        s=patch(self.prior)
        blocks=[]
        for start,end in (
            ('const bool v390_completed=', 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
            ('const bool v391_completed=', 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
            ('const bool v392_completed=', 'std::cout<<"V392_NAND_POST_CACHE_TRIAL'),
            ('const bool v393_completed=', 'std::cout<<"V393_NAND_NEXT_TRIAL'),
        ):
            i=s.index(start);j=s.index(end,i);blocks.append(s[i:j])
        free=(
            '#include <cstdint>\n'
            'struct Context{uint32_t pc=0u,lr=0u;};\n'
            'namespace nwii{namespace runtime{\n'
            'uint32_t v390_call_seen=0u,v390_call_pc=0u,v390_call_lr=0u;\n'
            'uint32_t v391_kind=0u,v391_calls=0u,v391_next_pc=0u,v391_next_lr=0u;\n'
            'uint32_t v392_kind=0u,v392_calls=0u,v392_next_pc=0u,v392_next_lr=0u;\n'
            'uint32_t v393_next_seen=0u,v393_next_pc=0u,v393_next_lr=0u;\n'
            'uint32_t v394_isfs_seen=0u;\n}}\n'
            'int main(){Context c{}; const bool v389_completed=true;\n'
            +'\n'.join(blocks)+'\nreturn int(v393_completed);}\n'
        )
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'free.cpp'
            source.write_text(free,encoding='utf-8')
            result=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                     '-Werror','-Wno-unused-variable','-fsyntax-only',str(source)],
                    capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr[-1600:])
    def test_prior_nested_guest_path_drift_rejected(self):
        for altered in (
            self.prior.replace('V393_NAND_NEXT_CALL guest=','lost'),
            self.prior.replace('V393_NAND_NEXT_TRIAL first=','lost'),
            self.prior.replace('V392_NAND_POST_CACHE_EVENT kind=','lost'),
            self.prior.replace('V389_NAND_FLAG_ACK before=','lost'),
            self.prior.replace(STOP,'lost'),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):patch(altered)
if __name__=="__main__":unittest.main()
