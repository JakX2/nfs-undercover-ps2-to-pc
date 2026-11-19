#!/usr/bin/env python3
"""Original-free V109 assertion classification across evolving overlays."""
import unittest
from pathlib import Path
from classify_v38_native_failure import STRING
from derive_v109_sc_nonempty_harness import derive
from diagnose_sc_nonempty_v109 import describe

class V109Messages(unittest.TestCase):
    def test_public_label_roundtrip(self):
        source=derive(Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8"))
        catalog=sorted(set(STRING.findall(source)))
        for label in ("V109 original nonempty SC second copy input differs",
                      "V109 original nonempty SC copy did not reach next length helper"):
            self.assertIn(label,catalog)
            self.assertEqual(describe(catalog.index(label)+1),label)
        with self.assertRaises(ValueError):describe(0)
        with self.assertRaises(ValueError):describe(len(catalog)+1)

if __name__=="__main__":unittest.main()
