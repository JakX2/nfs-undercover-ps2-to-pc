#!/usr/bin/env python3
"""V127 original-free generator and full code guard regression."""
from pathlib import Path
import unittest
from derive_v125_sc_helper_generator import derive as previous
from derive_v127_osinit_first_bl_generator import derive,EDITS
HERE=Path(__file__).resolve().parent

class GeneratorV127(unittest.TestCase):
    def test_guards_replace_synthetic_stop_only(self):
        source=(HERE/"generate_start_to_ipc_ack_v77.cpp").read_text()
        base=previous(source)
        actual=derive(source)
        expected=base
        for old,new in EDITS:
            count=2 if old=="os_has(OS_RET_STOP,0x44000002u)" else 1
            self.assertEqual(expected.count(old),count,old[:60])
            expected=expected.replace(old,new)
        self.assertEqual(actual,expected)
        self.assertEqual(actual.count("os_original_bl(OS_RET_STOP)"),2)
        self.assertIn("!os_has(OS_RET_STOP+4u,0x4e800020u)",actual)
        self.assertIn("os_has(0x8052097cu,0x44000002u)",actual)
        self.assertIn("V125 original SC helper translated geometry differs",actual)
        self.assertIn("V125_BAD_BRANCH site=",actual)
        self.assertNotIn("os_has(OS_RET_STOP,0x44000002u)",actual)
if __name__=="__main__":
    unittest.main()
