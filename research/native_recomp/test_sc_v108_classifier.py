#!/usr/bin/env python3
"""V108 public classifier, deliberately independent of owner binaries."""
from pathlib import Path
import unittest
from classify_v38_native_failure import STRING
from derive_v108_sc_literal_restore_harness import derive
from diagnose_sc_literal_restore_v108 import describe
HERE=Path(__file__).resolve().parent
class PublicV108(unittest.TestCase):
    def test_catalog(self):
        source=derive((HERE/"test_start_to_ipc_ack_v77.cpp").read_text())
        strings=sorted(set(STRING.findall(source)))
        self.assertIn("V108 SC literal provenance is not an omitted initialized data span",strings)
        self.assertIn("V108 restored initialized SC bytes differ from owner literal",strings)
        for name in ("V108 SC literal provenance is not an omitted initialized data span",
                     "V108 restored initialized SC bytes differ from owner literal"):
            self.assertEqual(describe(strings.index(name)+1),name)
        with self.assertRaises(ValueError):describe(0)
        with self.assertRaises(ValueError):describe(len(strings)+1)
    def test_known_failed_id(self):
        self.assertTrue(describe(530))
if __name__=="__main__":unittest.main()
