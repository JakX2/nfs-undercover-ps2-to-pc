#!/usr/bin/env python3
"""Independent synthetic-only tests of private-manifest validation."""
import unittest
from check_original_manifest import validate


def example():
    return {"schema": "uc-wii-function-index-v1", "language": "PowerPC:BE:32:Gekko_Broadway",
            "functions": [{"pc": "0x8000403C", "size": 8, "calls": ["0x80004050"]},
                          {"pc": "0x80004050", "size": 8, "calls": []}]}


class ValidateTests(unittest.TestCase):
    def test_valid_original_free_sample(self):
        self.assertEqual(validate(example(), minimum=2), (2, 1))

    def test_language_mismatch_rejected(self):
        x = example(); x["language"] = "PowerPC:BE:32:default"
        with self.assertRaises(ValueError):
            validate(x, minimum=2)

    def test_entry_missing_rejected(self):
        x = example(); x["functions"][0]["pc"] = "0x80004040"
        with self.assertRaises(ValueError):
            validate(x, minimum=2)

    def test_rejects_duplicate_entry(self):
        x = example(); x["functions"][1]["pc"] = "0x8000403C"
        with self.assertRaises(ValueError):
            validate(x, minimum=2)

    def test_missing_calls_rejected(self):
        x = example(); x["functions"][0]["calls"] = []
        with self.assertRaises(ValueError):
            validate(x, minimum=2)

    def test_default_needs_original_scale(self):
        with self.assertRaises(ValueError):
            validate(example())


if __name__ == "__main__":
    unittest.main()
