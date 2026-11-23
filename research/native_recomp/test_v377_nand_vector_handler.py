#!/usr/bin/env python3
"""V377 original-free validation: preserve V160 SC oracle and NAND vector resume."""
import unittest
from derive_v377_nand_vector_handler import (
    HEAD,V160,V375,V376,STATE,TRACE,MARKER,VECTOR,TRIAL,
    select_v160,wrap_v160,patch,
)
OLD=(
  '       check(nwii::runtime::v160_vector_seen==1u&&\n'
  '             nwii::runtime::v160_handler_seen==1u&&\n'
  '             nwii::runtime::v159_vector_seen==1u&&\n'
  '             nwii::runtime::v158_rfi_seen==1u&&\n'
  '             c.pc==0x80526ce0u&&!c.is_running,\n'
  '             "V160 did not execute original SC Y1 exception vector to handler");'
)
SOURCE=(
  '#include "native_external_irq.h"\n'
  'bool v250_candidate_mode=false;unsigned v250_nand_seen=0;\n'
  'auto phase(){return v250_candidate_mode&&v250_nand_seen==1u;}\n'
  'auto irq74_vector=1;\n'
  'void prior(){const char* a="V376_NAND_VECTOR n=";\n'
  'const char* b="V375_NAND_Y1_BOUNDARY n=";}\n'
  +HEAD+'\n}\n'
  'void owner(){\n'
  '  for(unsigned trial=0;trial<16;++trial){\n'
  +OLD+'\n'
  '  }\n'
  '}\n'
)
class Tests(unittest.TestCase):
    def test_only_sc_oracle_is_scoped(self):
        start,end,old=select_v160(SOURCE)
        self.assertEqual(old,OLD)
        self.assertEqual(SOURCE[start:end],OLD)
        scoped=patch(SOURCE)
        self.assertEqual(scoped.count(V160),1)
        self.assertIn(OLD,scoped)
        self.assertIn('}else{\n'+OLD,scoped)
        self.assertIn('continue; // finish this authenticated NAND-only bounded trial',scoped)
        self.assertIn('try{run_game(c);}',scoped)
        self.assertIn('V377 original NAND Y1 vector resumption prerequisite missing',scoped)
        self.assertIn('c.is_running=true;',scoped)
        self.assertIn('c.pc==undercover::wii::ExternalVector',scoped)
        self.assertEqual(scoped.replace(STATE+HEAD+TRACE,HEAD,1).
                         replace(wrap_v160(old),old,1),SOURCE)
    def test_original_vector_and_real_handler_only(self):
        for required in (
            'addr==undercover::wii::ExternalVector',
            'irq74_vector[i]', 'ctx.srr0==v377_resume',
            'ctx.srr1==v377_srr1', 'ctx.gpr==v377_gprs',
            'return; // execute authentic translated guest vector instructions',
            'addr==0x80526ce0u','ctx.gpr[3]==4u',
            'ctx.mmu.read32(frame+408u)==v377_resume',
            'ctx.mmu.read32(frame+412u)==v377_srr1',
            'ctx.inst_count>v377_start_inst',
            'ctx.is_running=false;throw ExceptionStop{};',
        ):
            self.assertIn(required,TRACE,required)
        for forbidden in (
            'ipc70_bus.tick(', 'service_one(', 'ipc70_bus.write32(',
            'ipc70_ram.write32(', 'ctx.pc=', 'ctx.msr=', 'ctx.gpr[3]=',
            'ctx.srr0=', 'ctx.srr1=', 'run_game(ctx)', 'ctx.mmu.write',
            'StmIos::Reply', 'StmIos::Invalid',
        ):
            if forbidden.endswith('='):
                import re
                self.assertIsNone(re.search(r'\b'+re.escape(forbidden)+r'(?!=)',TRACE))
            else:
                self.assertNotIn(forbidden,TRACE,forbidden)
    def test_fails_closed_on_non_unique_or_altered_sc_proof(self):
        for variant in (
            SOURCE.replace(HEAD,''),
            SOURCE+HEAD,
            SOURCE.replace(V375,'lost'),
            SOURCE.replace(V376,'lost'),
            SOURCE.replace(V160,'changed'),
            SOURCE.replace('nwii::runtime::v160_handler_seen','other'),
            SOURCE+OLD,
            patch(SOURCE),
        ):
            with self.assertRaises(ValueError):
                patch(variant)
if __name__=='__main__':
    unittest.main()
