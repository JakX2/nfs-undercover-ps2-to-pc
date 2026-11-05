"""Synthetic tests, no original proprietary LUT required."""
import math
import unittest
from angle16_reference import angle16, angle_degrees, signed16


def synthetic_atan_table():
    # Independent, calculated stand-in: NOT the original copyrighted table.
    return tuple(round(math.atan(i / 256) * 65536 / (2 * math.pi))
                 for i in range(257))


class SharedAngleReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = synthetic_atan_table()

    def test_cardinal_directions(self):
        expected = {(1, 0): 0x0000, (0, 1): 0x4000,
                    (-1, 0): 0x8000, (0, -1): 0xC000}
        for pair, value in expected.items():
            self.assertEqual(angle16(*pair, self.table), value)

    def test_diagonals(self):
        expected = {(1, 1): 0x2000, (-1, 1): 0x6000,
                    (-1, -1): 0xA000, (1, -1): 0xE000}
        for pair, value in expected.items():
            self.assertEqual(angle16(*pair, self.table), value)

    def test_origin(self):
        self.assertEqual(angle16(0, 0, self.table), 0)

    def test_signed_conversion(self):
        self.assertEqual(signed16(0x8000), -32768)
        self.assertEqual(angle_degrees(0xA000), -135.0)

    def test_error_invalid_table(self):
        with self.assertRaises(ValueError):
            angle16(1, 0, (0, 1))

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            angle16(float("nan"), 1, self.table)

    def test_quadrant_symmetry(self):
        for y in (0.1, 0.5, 2):
            self.assertEqual((angle16(1, y, self.table) +
                              angle16(1, -y, self.table)) & 0xffff, 0)


if __name__ == "__main__":
    unittest.main()
