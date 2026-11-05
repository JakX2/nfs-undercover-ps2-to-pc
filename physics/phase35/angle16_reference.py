"""Source-only reference for the shared PS2 fixed-angle lookup.

Pass a table of 257 unsigned 16-bit values from the user's locally owned
original PS2 game. The original table bytes are NOT stored in this repo.

This models ordinary finite input and assumes MIPS FCSR round-to-nearest.
It is NOT a PC game patch or a complete steering simulation.
"""
import math
import struct


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def signed16(value):
    return ((value & 0xffff) ^ 0x8000) - 0x8000


def _quadrant(angle, q):
    if q == 0:
        return angle & 0xffff
    if q == 3:
        return (-angle) & 0xffff
    if q == 1:
        return (0x8000 - angle) & 0xffff
    return (angle - 0x8000) & 0xffff


def angle16(x, y, table):
    """MIPS PS2 bATan-style angle equivalent to atan2(y,x) in turn units.

    Near-unity values that round to the final interpolation endpoint are
    intentionally rejected rather than reading past the 257-entry table.
    """
    if len(table) != 257:
        raise ValueError("expected 257 original LUT entries")
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("nonfinite input")
    x, y = f32(x), f32(y)
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("float32 overflow")
    quadrant = 0
    if x < 0:
        x = -x
        quadrant = 1
    if y < 0:
        y = -y
        quadrant ^= 3
    if x == y:
        return _quadrant(0x2000 if y else 0, quadrant)
    if y < x:
        ratio = f32(y / x)
        supplement = 0
    else:
        ratio = f32(x / y)
        supplement = 0x4000
    integer = round(f32(ratio * f32(65536.0)))
    index = integer >> 8
    fraction = integer & 0xff
    if not 0 <= index < 256:
        raise ValueError("endpoint overread not modeled")
    first, second = table[index:index+2]
    low_angle = first + (((second - first) * fraction) >> 8)
    octant_angle = supplement - low_angle if supplement else low_angle
    return _quadrant(octant_angle, quadrant)


def angle_degrees(raw_angle):
    return f32(f32(signed16(raw_angle) * f32(1/65536)) * f32(360.0))
