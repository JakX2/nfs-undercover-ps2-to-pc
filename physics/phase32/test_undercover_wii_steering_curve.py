"""Self-contained regression tests. The original game executable stays local."""
import math
import os
import unittest
from pathlib import Path
from undercover_wii_steering_curve import (
    EXPECTED_SHA256, at, early_transformed_input, elf32_be_sections,
    ppc_bl_target, signed_power, signed_square, verify_elf,
)


class TestSteeringModel(unittest.TestCase):
    def test_sign(self):
        for x in (0.1, 0.4, 0.6, 1.0):
            self.assertAlmostEqual(signed_power(-x, 1.15), -signed_power(x, 1.15))
            self.assertAlmostEqual(signed_square(-x), -signed_square(x))

    def test_reference_half_stick(self):
        self.assertAlmostEqual(signed_power(0.5, 1.15), 0.450625231, places=7)
        self.assertAlmostEqual(signed_square(0.5), 0.25)

    def test_deadzone_is_after_transform(self):
        self.assertAlmostEqual(early_transformed_input(0.2, use_power=True),
                               signed_power(0.2, 1.15))
        self.assertEqual(early_transformed_input(0.2, use_power=False), 0.0)
        self.assertEqual(early_transformed_input(0.0), 0.0)
        self.assertEqual(early_transformed_input(-0.2, use_power=False), 0.0)

    def test_endpoints(self):
        for flag in (True, False):
            self.assertEqual(early_transformed_input(1.0, use_power=flag), 1.0)
            self.assertEqual(early_transformed_input(-1.0, use_power=flag), -1.0)

    def test_power_more_than_square_on_unit_interval(self):
        for x in (0.15, 0.4, 0.6, 0.9):
            self.assertGreater(signed_power(x, 1.15), signed_square(x))

    def test_ppc_relative_bl(self):
        va = 0x80324ce0
        inst = (0x4822c341).to_bytes(4, 'big')
        self.assertEqual(ppc_bl_target(inst, va), 0x80551020)
        with self.assertRaises(ValueError):
            ppc_bl_target((0x60000000).to_bytes(4, 'big'), va)

    def test_non_elf(self):
        with self.assertRaisesRegex(ValueError, 'ELF'):
            verify_elf(b'hello', verify_sha=False)

    def test_missing_elf_sha(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            verify_elf(b'not the game', verify_sha=True)

    def test_real_elf_if_available(self):
        path_value = os.environ.get('UC_WII_ELF')
        if not path_value:
            self.skipTest('Set UC_WII_ELF to a locally owned ELF for binary verification')
        raw = Path(path_value).read_bytes()
        info = verify_elf(raw)
        self.assertEqual(info['sha256'], EXPECTED_SHA256)
        self.assertEqual(info['checked_direct_calls'], 7)
        self.assertEqual(info['checked_instruction_signatures'], 15)
        self.assertAlmostEqual(info['constants']['exponent'], 1.15, places=6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
