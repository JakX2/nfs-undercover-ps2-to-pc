#!/usr/bin/env python3
"""V109 original-free classifier regression."""
import unittest
from diagnose_sc_nonempty_v109 import describe
class Test(unittest.TestCase):
    def test_catalog(self):
        self.assertEqual(describe(266),describe(266))
        with self.assertRaises(ValueError):describe(0)
        with self.assertRaises(ValueError):describe(99999)
if __name__=="__main__":unittest.main()
