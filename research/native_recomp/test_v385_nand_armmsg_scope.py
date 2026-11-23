#!/usr/bin/env python3
"""V385 first-SC ARMMSG scope: original-free source reversibility tests."""
import unittest
from derive_v385_nand_armmsg_scope import patch,OLD,NEW,MARKER

SOURCE=(
    'bool v250_candidate_mode=false;'
    'unsigned v250_nand_seen=0,v384_read_seen=0;\n'
    'auto run(){const char* a="V385_NAND_SECOND_READ caller=";\n'
    'const char* b="V384_NAND_REPLY_READ caller=";\n'
    'auto x=ipc70_bus.read32(1); auto y=ipc70_bus.read32(2);\n'
    'if(v250_candidate_mode&&v250_nand_seen&&v384_read_seen){\n'
    +OLD+'\n'
    '}}\n'
)
class Tests(unittest.TestCase):
    def test_preserve_first_sc_and_check_real_nand_armmsg(self):
        out=patch(SOURCE)
        self.assertEqual(out.count(MARKER),1)
        self.assertIn(OLD.strip().split('\n')[0].strip(),out)
        self.assertIn('++wake80_armmsg;',out)
        self.assertIn('v250_candidate_mode&&v250_nand_seen==1u&&v384_read_seen==1u',out)
        self.assertIn('const bool v385_coherent=result.has_value()',out)
        self.assertIn('*result==*v385_arm',out)
        self.assertIn('((*v385_ctrl&V385Mail::Y1)!=0u)',out)
        self.assertIn('check(v385_coherent&&v385_y1',out)
        self.assertEqual(out.replace(NEW,OLD,1),SOURCE)
        for forbidden in ('ipc70_bus.write32(', 'service_one(', 'ipc70_bus.tick(',
                          'ctx.pc=', 'ctx.gpr=', 'StmIos::Reply','StmIos::Invalid'):
            self.assertNotIn(forbidden,NEW)
    def test_fail_closed_on_changed_or_multiple_v80_observers(self):
        for s in (
            SOURCE.replace('submit72_phys','other'),
            SOURCE.replace('wake80_armmsg','other'),
            SOURCE.replace('V385_NAND_SECOND_READ caller=','lost'),
            SOURCE.replace('V384_NAND_REPLY_READ caller=','lost'),
            SOURCE.replace('v384_read_seen','missing'),
            SOURCE+OLD,
            patch(SOURCE),
        ):
            with self.assertRaises(ValueError):patch(s)
if __name__=='__main__':
    unittest.main()
