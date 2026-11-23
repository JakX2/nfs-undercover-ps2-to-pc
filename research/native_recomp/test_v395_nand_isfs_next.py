#!/usr/bin/env python3
"""V395 original-free unchanged guest callback execution regression suite."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v394_nand_isfs_entry import Tests as Fixture394
from derive_v394_nand_isfs_entry import patch as v394
from derive_v395_nand_isfs_next import patch,TRACE,STOP,CONTINUE,MARKER,TRIAL

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture394.setUpClass()
        cls.prior=v394(Fixture394.prior)
    def test_no_fake_nand_completion(self):
        s=patch(self.prior)
        self.assertEqual(s.count(MARKER),1)
        self.assertEqual(s.count(TRIAL),1)
        self.assertNotIn(STOP,s)
        self.assertIn(CONTINUE,s)
        self.assertIn('V394_NAND_ISFS_ENTRY guest=',s)
        self.assertIn('V393_NAND_NEXT_CALL guest=',s)
        self.assertIn('V389_NAND_FLAG_ACK before=',s)
        self.assertIn('check(v395_completed,',s)
        self.assertEqual(s.count('nwii::runtime::v395_next_seen=0u;'),1)
        self.assertLess(s.index('nwii::runtime::v395_next_seen=0u;'),
                        s.index('c.is_running=true; // execute up to 16'))
    def test_guest_abi_and_only_observed_indirect_nand_target(self):
        for wanted in (
            'v394_context_seen==1u&&v394_isfs_seen==1u',
            'ctx.lr>=0x804f0e04u&&ctx.lr<0x804f0f84u',
            'ctx.inst_count>v395_isfs_inst',
            '((*ctrl&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)==0u)',
            '!ipc70_bus.external_irq_level()',
            'data<=0xfffffef8u',
            'ctx.mmu.get_ptr(data+263u)',
            'ctx.mmu.read32(data+256u)==addr',
            'ctx.gpr[4]==ctx.mmu.read32(data+260u)',
            'addr==0x8051e06cu&&ctx.lr==0x804f0f54u',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):self.assertIn(wanted,TRACE,wanted)
        for forbidden in ('service_one(', 'ipc70_bus.write32(', 'ipc70_bus.tick(',
                          'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=',
                          'ctx.gpr[3]=', 'StmIos::Reply', 'StmIos::Invalid'):
            if forbidden.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:self.assertNotIn(forbidden,TRACE)
    def test_inherited_original_cxx_checks_build_with_werror(self):
        compiler=shutil.which('g++')
        if compiler is None:self.skipTest('g++ not available')
        source=patch(self.prior)
        predicates=[]
        for start,finish in (
            ('const bool v390_completed=', 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
            ('const bool v391_completed=', 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
            ('const bool v392_completed=', 'std::cout<<"V392_NAND_POST_CACHE_TRIAL'),
            ('const bool v393_completed=', 'std::cout<<"V393_NAND_NEXT_TRIAL'),
            ('const bool v394_completed=', 'std::cout<<"V394_NAND_ISFS_TRIAL'),
        ):
            i=source.index(start);j=source.index(finish,i);predicates.append(source[i:j])
        fixture=(
            '#include <cstdint>\nstruct Context{uint32_t pc=0u,lr=0u;};\n'
            'namespace nwii{namespace runtime{\n'
            'uint32_t v390_call_seen=0u,v390_call_pc=0u,v390_call_lr=0u;\n'
            'uint32_t v391_kind=0u,v391_calls=0u,v391_next_pc=0u,v391_next_lr=0u;\n'
            'uint32_t v392_kind=0u,v392_calls=0u,v392_next_pc=0u,v392_next_lr=0u;\n'
            'uint32_t v393_next_seen=0u,v393_next_pc=0u,v393_next_lr=0u;\n'
            'uint32_t v394_isfs_seen=0u;\n'
            'uint32_t v395_next_seen=0u,v395_next_pc=0u,v395_next_lr=0u;\n'
            '}}\nint main(){Context c{};const bool v389_completed=true;\n'
            +'\n'.join(predicates)+'\nreturn int(v394_completed);}\n'
        )
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'original_free.cpp'
            file.write_text(fixture,encoding='utf-8')
            proc=subprocess.run([compiler,'-std=c++20','-Wall','-Wextra',
                    '-Werror','-Wno-unused-variable','-fsyntax-only',str(file)],
                    capture_output=True,text=True,check=False)
            self.assertEqual(proc.returncode,0,proc.stderr[-1600:])
    def test_source_seam_drift_and_double_apply_fail(self):
        for broken in (
            self.prior.replace('V394_NAND_ISFS_ENTRY guest=','lost'),
            self.prior.replace('V394_NAND_ISFS_TRIAL context=','lost'),
            self.prior.replace('V392_NAND_POST_CACHE_EVENT kind=','lost'),
            self.prior.replace('V389_NAND_FLAG_ACK before=','lost'),
            self.prior.replace(STOP,'lost'),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):patch(broken)
if __name__=="__main__":unittest.main()
