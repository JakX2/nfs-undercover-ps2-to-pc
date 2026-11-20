#!/usr/bin/env python3
"""V128 owner-free generator extension preserving all inherited call guards."""
import unittest
from pathlib import Path
from derive_v127_osinit_first_bl_generator import derive as previous
from derive_v128_next_function_generator import derive,OLD,NEW
HERE=Path(__file__).resolve().parent

class V128Generator(unittest.TestCase):
    def test_original_function_ownership(self):
        original=(HERE/"generate_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(original)
        self.assertEqual(prior.count(OLD),1)
        actual=derive(original)
        self.assertEqual(actual,prior.replace(OLD,NEW,1))
        for marker in ("V128 original 71-instruction function geometry differs",
                       "V128 original OSInit call target differs",
                       "f128.size()==71u",
                       "f128.back().address==0x8052f948u",
                       "V125 original SC helper translated geometry differs",
                       "os_original_bl(OS_RET_STOP)"):
            self.assertIn(marker,actual)
if __name__=="__main__":
    unittest.main()
