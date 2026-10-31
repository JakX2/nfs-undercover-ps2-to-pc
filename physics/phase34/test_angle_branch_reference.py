"""Synthetic tests only; original-game ISA verification is in local Phase34 ZIP."""
import unittest
from angle_branch_reference import (branch_arguments, f32, signed16,
                                    signed_square, intermediate_limit)


class AngleBranchReferenceTests(unittest.TestCase):
    def test_square_preserves_sign(self):
        self.assertAlmostEqual(signed_square(0.5), 0.25)
        self.assertAlmostEqual(signed_square(-0.5), -0.25)

    def test_positive_branch(self):
        self.assertEqual(branch_arguments(0.2), ("positive", f32(0.2), f32(3.8)))

    def test_negative_branch(self):
        self.assertEqual(branch_arguments(-0.2), ("negative", f32(0.2), 11.0))

    def test_center_branch(self):
        for x in (-0.05, 0.0, 0.05):
            self.assertEqual(branch_arguments(x), ("center", None, None))

    def test_boundary_strict(self):
        self.assertEqual(branch_arguments(f32(0.1))[0], "center")
        self.assertEqual(branch_arguments(-f32(0.1))[0], "center")
        self.assertEqual(branch_arguments(0.101)[0], "positive")
        self.assertEqual(branch_arguments(-0.101)[0], "negative")

    def test_angle16_sign_extension(self):
        self.assertEqual(signed16(0x2000), 8192)
        self.assertEqual(signed16(0xffff), -1)
        self.assertEqual(signed16(0x8000), -32768)

    def test_lookup_to_degrees(self):
        r = intermediate_limit(0.4, 0, 0x2000)
        self.assertEqual(r["base_degrees"], 45.0)
        self.assertEqual(r["limit_degrees"], 45.0)

    def test_dynamic_scaling(self):
        self.assertEqual(intermediate_limit(0.4, 0.5, 0x2000)["limit_degrees"], 55)
        self.assertEqual(intermediate_limit(0.4, -0.5, 0x2000)["limit_degrees"], 33.75)

    def test_center_without_lookup(self):
        self.assertEqual(intermediate_limit(0, 0)["limit_degrees"], 55.0)

    def test_no_fabricated_angle(self):
        with self.assertRaisesRegex(ValueError, "required"):
            intermediate_limit(0.2, 0)


if __name__ == "__main__":
    unittest.main()
