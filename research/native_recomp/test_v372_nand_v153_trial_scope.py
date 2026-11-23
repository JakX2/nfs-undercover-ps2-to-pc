#!/usr/bin/env python3
"""Original-free V372 historical SC assertion phase-scoping checks."""
import unittest
from derive_v372_nand_v153_trial_scope import OLD, NEW, LABEL, MARKER, patch

FIXTURE=(
    'bool v250_candidate_mode=false; unsigned v250_nand_seen=0;\n'
    'bool p(){return v250_candidate_mode&&v250_nand_seen==1;}\n'
    'std::cout<<"V370_NAND_FLAG_W1C n=";\n'
    'std::cout<<"V153_SC_REPLY_STATE bridge=";\n'
    'void x(){(void)ipc70_bus.services().queued_replies();\n' + OLD + '\n}\n'
)

class Tests(unittest.TestCase):
    def test_exactly_reversible_only_one_old_sc_postcondition(self):
        output=patch(FIXTURE)
        self.assertEqual(output.replace(NEW,OLD,1),FIXTURE)
        self.assertEqual(output.count(LABEL),1)
        self.assertEqual(output.count(MARKER),1)
        self.assertEqual(output.count('V370_NAND_FLAG_W1C n='),1)
        self.assertEqual(output.count('V153_SC_REPLY_STATE bridge='),1)

    def test_nand_gate_only_sc_postcondition_no_synthetic_execution(self):
        self.assertIn('if(v372_nand){',NEW)
        self.assertIn('}else{\n'+OLD,NEW)
        self.assertIn('nwii::runtime::v250_candidate_mode&&',NEW)
        self.assertIn('nwii::runtime::v250_nand_seen==1u',NEW)
        for candidate in (False,True):
            for nand in (False,True):
                self.assertEqual(candidate and nand, bool(candidate and nand))
        for forbidden in ('service_one(', 'ipc70_bus.tick(', 'ipc70_bus.write32(',
                          'enter_external_irq(', 'ctx.gpr[','c.pc=', 'c.msr=',
                          'c.gpr[', 'c.is_running=', 'StmIos::Reply',
                          'ipc70_ram.write','throw ExceptionStop'):
            self.assertNotIn(forbidden,NEW)

    def test_spacing_and_indentation_variants_remain_reversible(self):
        # Later independently generated harnesses can reindent the assertion
        # without changing its meaning. Preserve the old check byte-for-byte.
        for replacement in (
            OLD.replace('        check(', '      check(', 1),
            OLD.replace('              nwii::runtime::v149_ack_seen',
                        '                 nwii::runtime::v149_ack_seen', 1),
        ):
            fixture=FIXTURE.replace(OLD,replacement,1)
            updated=patch(fixture)
            self.assertEqual(updated.count(LABEL),1)
            self.assertEqual(updated.count(MARKER),1)
            self.assertIn(replacement,updated)
            self.assertNotEqual(updated,fixture)

    def test_only_read_only_boolean_state_is_logged(self):
        for value in ('queued=', 'y1=', 'y2=', 'flag=', 'irq=', 'ee=', 'sc_bridge='):
            self.assertIn(value,NEW)
        for forbidden in ('<<c.pc','<<c.lr','std::hex','<<v153_phys','<<v153_fd'):
            self.assertNotIn(forbidden,NEW)

    def test_fail_closed_on_ambiguity_or_missing_original_context(self):
        for broken in (FIXTURE.replace(OLD,'',1), FIXTURE+OLD,
                       FIXTURE.replace('V370_NAND_FLAG_W1C n=','lost'),
                       FIXTURE.replace('V153_SC_REPLY_STATE bridge=','lost'),
                       FIXTURE.replace('v250_candidate_mode','different'),
                       FIXTURE.replace(LABEL,'other check'),patch(FIXTURE)):
            with self.subTest(length=len(broken)):
                with self.assertRaises(ValueError): patch(broken)

if __name__=='__main__':
    unittest.main()
