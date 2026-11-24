#!/usr/bin/env python3
import unittest
from windows_full_build_v426 import owner_scope,audit_owner_start,BuildError
from audit_v419_full_start import STAGES as START,RESULT as START_RESULT
from audit_v425_full_hardware import STAGES as HW,RESULT as HW_RESULT

class Tests(unittest.TestCase):
    def test_scope_contract(self):
        self.assertEqual(owner_scope('startup',True),((),'prepare_v419_full_start.py'))
        self.assertEqual(owner_scope('startup',False),((),'prepare_v419_full_start.py'))
        self.assertEqual(owner_scope('hardware',False),(('apply_hid_state_v18','apply_fpscr_v19'),'prepare_v425_full_hardware.py'))
        for scope,synthetic in (('hardware',True),('cache',True),('bogus',True)):
            with self.assertRaises(BuildError):owner_scope(scope,synthetic)
    def test_exact_scope_gate(self):
        start=b'\n'.join(START+[START_RESULT])+b'\n';hardware=b'\n'.join(HW+[HW_RESULT])+b'\n'
        self.assertTrue(audit_owner_start(start,0,'startup')[1]);self.assertTrue(audit_owner_start(hardware,0,'hardware')[1])
        self.assertFalse(audit_owner_start(start,0,'hardware')[1]);self.assertFalse(audit_owner_start(hardware,0,'startup')[1])
        for rc in (1,124,134,0xc0000005,-1):
            self.assertFalse(audit_owner_start(hardware,rc,'hardware')[1])
        self.assertIn('stages=8',audit_owner_start(b'\n'.join(HW[:8]),82,'hardware')[0])
if __name__=='__main__':unittest.main()
