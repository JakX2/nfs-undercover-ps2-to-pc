#!/usr/bin/env python3
"""V392 bounded original NAND repeated-cache successor original-free tests."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_v391_nand_post_ack_next import Tests as Fixture391
from derive_v391_nand_post_ack_next import patch as v391
from derive_v392_nand_post_cache import patch,TRACE,STOP,CONTINUE,MARKER,TRIAL

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture391.setUpClass()
        cls.prior=v391(Fixture391.prior)
    def test_original_guest_cache_chain_only_not_forced_context(self):
        out=patch(self.prior)
        self.assertEqual(out.count(MARKER),1)
        self.assertEqual(out.count(TRIAL),1)
        self.assertNotIn(STOP,out)
        self.assertIn(CONTINUE,out)
        self.assertIn("V391_NAND_POST_ACK_EVENT kind=",out)
        self.assertIn("V390_NAND_POST_ACK guest=",out)
        self.assertIn("V389_NAND_FLAG_ACK before=",out)
        self.assertIn("check(v390_completed,",out)
        self.assertIn("check(v391_completed,",out)
        self.assertIn("check(v392_completed,",out)
        self.assertEqual(out.count('nwii::runtime::v392_kind=0u;'),1)
        self.assertLess(out.index('nwii::runtime::v392_kind=0u;'),
                        out.index('c.is_running=true; // execute up to 16'))
    def test_original_hardware_and_read_only_target_classification(self):
        for token in (
            'v391_kind==1u&&v392_kind==0u',
            'ctx.inst_count>v392_start_inst',
            '((*ctrl&(M::Y1|M::Y2))==0u)',
            '((*flag&H::IPC_PPC)==0u)',
            '!ipc70_bus.external_irq_level()',
            'ctx.mmu.read32(IRQ_TABLE+27u*4u)==0x80519318u',
            'ctx.lr>=0x805190c0u&&ctx.lr<0x80519318u',
            'addr==0x80522294u',
            'addr==0x80522af4u||addr==0x805228ccu',
            'addr==0x804f0e04u',
            'v392_calls==24u',
            'ctx.is_running=false;throw ExceptionStop{};'
        ):self.assertIn(token,TRACE,token)
        for blocked in ('service_one(', 'ipc70_bus.write32(', 'ipc70_bus.tick(',
                        'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=', 'ctx.lr=',
                        'ctx.gpr[3]=', 'StmIos::Reply','StmIos::Invalid'):
            if blocked.endswith('='):
                self.assertIsNone(re.search(r'\b'+re.escape(blocked)+r'(?!=)',TRACE))
            else:self.assertNotIn(blocked,TRACE)
        # V391 still stops safely on an observed 24-call budget.
        # Only the authenticated reply-handler-owned call continues.
        self.assertIn('if(v391_kind==1u){',CONTINUE)
        self.assertIn('return; // execute authentic post-ACK original guest callee',CONTINUE)
        self.assertIn('ctx.is_running=false;throw ExceptionStop{};',CONTINUE)
    def test_synthetic_guest_completion_predicates_compile_with_wall_werror(self):
        compiler=shutil.which('g++')
        if compiler is None:
            self.skipTest('g++ not installed on this host')
        output=patch(self.prior)
        predicates=[]
        for start_marker,end_marker in (
            ('const bool v390_completed=', 'std::cout<<"V390_NAND_POST_ACK_TRIAL'),
            ('const bool v391_completed=', 'std::cout<<"V391_NAND_POST_ACK_TRIAL'),
        ):
            start=output.index(start_marker)
            end=output.index(end_marker,start)
            predicates.append(output[start:end])
        harness=(
            '#include <cstdint>\n'
            'struct Context { uint32_t pc=0u,lr=0u; };\n'
            'namespace nwii { namespace runtime {\n'
            '  uint32_t v390_call_seen=0u,v390_call_pc=0u,v390_call_lr=0u;\n'
            '  uint32_t v391_kind=0u,v391_calls=0u;\n'
            '  uint32_t v391_next_pc=0u,v391_next_lr=0u;\n'
            '  uint32_t v392_kind=0u,v392_next_pc=0u,v392_next_lr=0u;\n'
            '} }\n'
            'int main() {\n'
            '  Context c{};\n'
            '  const bool v389_completed=true;\n'
            +'\n'.join(predicates)+
            '\n  return int(v391_completed);\n}\n'
        )
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'original_free_v392.cpp'
            file.write_text(harness,encoding='utf-8')
            proc=subprocess.run(
                [compiler,'-std=c++20','-Wall','-Wextra','-Werror',
                 '-Wno-unused-variable','-fsyntax-only',str(file)],
                capture_output=True,text=True,check=False)
            self.assertEqual(proc.returncode,0,proc.stderr[-1600:])

    def test_reject_prior_nand_ack_or_cache_witness_mutation(self):
        for altered in (
            self.prior.replace("V391_NAND_POST_ACK_EVENT kind=","missing"),
            self.prior.replace("V391_NAND_POST_ACK_TRIAL kind=","missing"),
            self.prior.replace("V390_NAND_POST_ACK guest=","missing"),
            self.prior.replace("V389_NAND_FLAG_ACK before=","missing"),
            self.prior.replace(STOP,"missing"),
            self.prior.replace("V391 original NAND post-ACK call trace did not reach real boundary","missing"),
            patch(self.prior)
        ):
            with self.assertRaises(ValueError):patch(altered)
if __name__=="__main__":unittest.main()
