#!/usr/bin/env python3
"""Read-only, exact-build identification of stripped PS2 human-steering functions.

Original game executables are local inputs. Only small instruction signatures
and addresses are included in this source. No execution or patching occurs.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

BUILDS = {
    "undercover_ps2": {
        "sha": "6c53252622348ee5981685420a27e6914e02757e739945f583940b8c35814646",
        "start": 0x4082B0, "end": 0x408770, "caller": 0x408A8C,
        "words": {
            0x4082B0: 0x27BDFF70, 0x408304: 0xC638008C,
            0x4083A0: 0xC621008C, 0x4083F4: 0x3C013DF5,
            0x4083F8: 0x3421C28F, 0x408400: 0x4600C045,
            0x408404: 0x4601C602, 0x40840C: 0x46001034,
            0x408414: 0x450300BD, 0x408464: 0x3C014073,
            0x408468: 0x34213333, 0x4084CC: 0x3C014130,
            0x408708: 0xE678019C, 0x408714: 0xE6750188,
            0x408728: 0x3C013B36, 0x40872C: 0x34210B6A,
            0x408768: 0x03E00008, 0x40876C: 0x27BD0090,
            0x408770: 0x27BDFFA0,
        },
        "calls": {0x4083C4: 0x408770, 0x408510: 0x172CB8,
                  0x408710: 0x459CE8, 0x408720: 0x3D14A8}
    },
    "carbon_ps2": {
        "sha": "1bcc9ff09b2dce748ab78453338c2733375a55ee4dd9a8ee534db9803a5e5d9b",
        "start": 0x3D58D8, "end": 0x3D5B88, "caller": 0x3D5FBC,
        "words": {
            0x3D58D8: 0x27BDFF90, 0x3D5920: 0xC636008C,
            0x3D59C0: 0xC621008C, 0x3D59C4: 0x3C014234,
            0x3D5B04: 0xE656019C, 0x3D5B14: 0xE6540188,
            0x3D5B80: 0x03E00008, 0x3D5B84: 0x27BD0070,
            0x3D5B88: 0x27BDFFA0,
        },
        "calls": {0x3D59E0: 0x3D5B88, 0x3D5A14: 0x3D5B88,
                  0x3D5B44: 0x3946C0}
    }
}


def load_segments(data):
    if len(data) < 0x54 or data[:6] != b"\x7fELF\x01\x01":
        raise ValueError("Expected little-endian ELF32")
    if struct.unpack_from("<H", data, 18)[0] != 8:
        raise ValueError("Not MIPS")
    phoff = struct.unpack_from("<I", data, 28)[0]
    size, count = struct.unpack_from("<HH", data, 42)
    if size < 32 or not 1 <= count <= 64:
        raise ValueError("Invalid program headers")
    segments = []
    for i in range(count):
        off = phoff + size * i
        if off + 32 > len(data):
            raise ValueError("Truncated headers")
        typ, filoff, addr, _, nbytes, _, _, _ = struct.unpack_from("<8I", data, off)
        if typ == 1:
            if filoff + nbytes > len(data):
                raise ValueError("Truncated LOAD segment")
            segments.append((addr, filoff, nbytes))
    if not segments:
        raise ValueError("No LOAD segment")
    return segments


def word_at(data, segments, addr):
    if addr % 4:
        raise ValueError("Unaligned address")
    for va, filoff, count in segments:
        d = addr - va
        if 0 <= d <= count - 4:
            return struct.unpack_from("<I", data, filoff + d)[0]
    raise ValueError(f"Unmapped address {addr:#x}")


def jal_target(word, address):
    if word >> 26 != 3:
        raise ValueError(f"Expected jal at {address:#x}")
    return ((address + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def callers(data, segments, target, bounds=None):
    result = []
    for va, filoff, count in segments:
        for offset in range(0, count & ~3, 4):
            pc = va + offset
            if bounds and not (bounds[0] <= pc < bounds[1]):
                continue
            word = struct.unpack_from("<I", data, filoff + offset)[0]
            if word >> 26 == 3 and jal_target(word, pc) == target:
                result.append(pc)
    return result


def verify(data, build):
    if build not in BUILDS:
        raise ValueError("Unknown PS2 build")
    spec = BUILDS[build]
    sha = hashlib.sha256(data).hexdigest()
    if sha != spec["sha"]:
        raise ValueError(f"Unsupported {build} SHA256: {sha}")
    seg = load_segments(data)
    for addr, expected in spec["words"].items():
        if word_at(data, seg, addr) != expected:
            raise ValueError(f"Signature mismatch at {addr:#x}")
    for addr, expected in spec["calls"].items():
        if jal_target(word_at(data, seg, addr), addr) != expected:
            raise ValueError(f"Call mismatch at {addr:#x}")
    if callers(data, seg, spec["start"]) != [spec["caller"]]:
        raise ValueError("Unexpected steering function callers")
    expected_helpers = sorted(addr for addr, dst in spec["calls"].items()
                              if dst == spec["end"])
    if callers(data, seg, spec["end"], (spec["start"], spec["end"])) != expected_helpers:
        raise ValueError("Unexpected steering helper callers")
    return {
        "build": build, "sha256": sha,
        "human_steering": f"0x{spec['start']:08X}",
        "length_bytes": spec["end"] - spec["start"],
        "instruction_checks": len(spec["words"]),
        "call_checks": len(spec["calls"]),
        "direct_caller": f"0x{spec['caller']:08X}",
        "helper_call_sites": [f"0x{x:08X}" for x in expected_helpers],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--uc", required=True, type=Path)
    p.add_argument("--carbon", required=True, type=Path)
    p.add_argument("--output", type=Path, default=Path("phase33_ps2_steering_verification.json"))
    args = p.parse_args()
    try:
        results = [verify(args.uc.read_bytes(), "undercover_ps2"),
                   verify(args.carbon.read_bytes(), "carbon_ps2")]
        args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    except (ValueError, OSError, struct.error) as exc:
        p.exit(1, f"FAIL: {exc}\n")
    for r in results:
        print("PASS", r["build"], r["human_steering"],
              r["instruction_checks"], "instruction checks",
              r["call_checks"], "call checks")


if __name__ == "__main__":
    main()
