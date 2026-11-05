"""Narrow reconstructed UC PS2 steering-angle branch (offline reference only).

Verified against original PS2 SLUS_218.01 in Phase34 research, not a port
of the full routine. The original angle lookup is deliberately opaque.
"""
import struct


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def signed_square(value):
    x = f32(value)
    return f32(x * abs(x))


def branch_arguments(state_48):
    """Select angle-helper arguments from the chassis state at +0x48.

    This field is NOT the player's steering input at chassis +0x8c.
    Do not map PS2 offsets directly to Carbon PC object layouts.
    """
    x = f32(state_48)
    if x > f32(0.1):
        return ("positive", x, f32(3.8))
    if x < -f32(0.1):
        return ("negative", f32(-x), f32(11.0))
    return ("center", None, None)


def signed16(value):
    value = value & 0xFFFF
    return (value ^ 0x8000) - 0x8000


def intermediate_limit(state_48, racer_160, angle_lookup_result=None):
    """Reconstruct the PRELIMINARY angle cap, not final wheel angle.

    For the noncenter branches, angle_lookup_result must be the actual
    game's 16-bit result, NOT a substituted Python math.atan2 value.
    """
    mode, arg1, arg2 = branch_arguments(state_48)
    if mode == "center":
        base = f32(55.0)
    else:
        if angle_lookup_result is None:
            raise ValueError("Original PS2 angle lookup result required")
        base = f32(f32(signed16(angle_lookup_result) * f32(1.0 / 65536.0)) * f32(360.0))
    scale = f32(1.0 + f32(f32(racer_160) * f32(0.5)))
    limit = f32(base * scale)
    return {"branch": mode, "argument_1": arg1, "argument_2": arg2,
            "base_degrees": base, "limit_degrees": min(55.0, limit),
            "scale": scale}


if __name__ == "__main__":
    for state in (-0.2, -0.1, 0, 0.1, 0.2):
        print(state, branch_arguments(state))
