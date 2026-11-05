#!/usr/bin/env python3
"""Validate selected Undercover Wii steering facts from a locally owned ELF.

Read-only and version-gated. No emulator, memory access, or modifications.
This proves the two input transforms and several routine boundaries, not
an entire steering port or which hardware device selects each branch.
"""
import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

EXPECTED_SHA256 = '1de2533575414a989e240db5cc99b528b7bf99f048f3d79022d9e1c8725d1653'
SDA2_BASE = 0x8073A5C0
FUNC = 0x80324B48
POW = 0x80551020
ATAN = 0x8007E5AC
# Short signature fragments: enough to gate this narrow research conclusion.
SIGNATURES = {
    0x80324B94: 'c3e4008c',  # original input: lfs f31,+0x8c(r4)
    0x80324CC4: '41820040',  # branch to signed-square input path
    0x80324CD8: 'fc20f850',  # negate negative input before pow
    0x80324CDC: 'c842a150',  # exponent: lfd f2,-24240(r2)
    0x80324CE4: 'fc000818',  # round pow result to float
    0x80324CE8: 'ffe00050',  # restore negative input sign
    0x80324CF4: 'c842a150',  # exponent for non-negative input
    0x80324CFC: 'ffe00818',  # round pow result to float
    0x80324D04: 'fc00fa10',  # fabs input
    0x80324D08: 'efff0032',  # signed-square: x * abs(x)
    0x80324CBC: 'c362a14c',  # dead-zone constant lfs -24244(r2)
    0x80324D0C: 'fc00fa10',  # check absolute transformed input
    0x80324FEC: 'd3fa011c',  # store transformed input in racer+0x11c
    0x80324FF0: 'd3ba0108',  # store later steering output in racer+0x108
    0x80325000: '387a0120',  # rolling history at racer+0x120
}
CALLS = {0x80324C90: 0x80325050, 0x80324CE0: POW,
         0x80324CF8: POW, 0x80324DA0: ATAN, 0x80324E2C: ATAN,
         0x80324FF4: 0x80378F98, 0x80325004: 0x802E1748}
CONSTANTS = {
    'exponent': ('>d', -24240, 1.15),
    'transformed_input_deadzone': ('>f', -24244, 0.12),
    'atan_positive_argument': ('>f', -24232, 3.8),
    'atan_negative_argument': ('>f', -24224, 11.0),
    'steering_angle_cap': ('>f', -24276, 55.0),
    'output_scale': ('>f', -24220, 1 / 360),
}


def elf32_be_sections(data):
    if data[:4] != b'\x7fELF' or data[4:6] != b'\x01\x02':
        raise ValueError('expected 32-bit big-endian ELF')
    shoff = struct.unpack_from('>I', data, 32)[0]
    entsize, count = struct.unpack_from('>HH', data, 46)
    if entsize < 40 or not (2 <= count <= 512):
        raise ValueError('invalid ELF sections')
    out = []
    for i in range(count):
        pos = shoff + i * entsize
        if pos + 40 > len(data):
            raise ValueError('ELF section table truncated')
        addr, off, size = struct.unpack_from('>III', data, pos + 12)
        out.append((addr, off, size))
    return out


def at(data, sections, va, count):
    for base, offset, size in sections:
        rel = va - base
        if 0 <= rel and rel + count <= size and offset + rel + count <= len(data):
            return data[offset + rel:offset + rel + count]
    raise ValueError(f'unmapped virtual address {va:#x}')


def ppc_bl_target(instruction, va):
    word = int.from_bytes(instruction, 'big')
    if word >> 26 != 18 or not (word & 1) or (word & 2):
        raise ValueError(f'not a relative PowerPC bl at {va:#x}')
    disp = word & 0x03fffffc
    if disp & 0x02000000:
        disp -= 0x04000000
    return (va + disp) & 0xffffffff


def verify_elf(data, verify_sha=True):
    digest = hashlib.sha256(data).hexdigest()
    if verify_sha and digest != EXPECTED_SHA256:
        raise ValueError(f'unsupported Undercover Wii ELF SHA256: {digest}')
    secs = elf32_be_sections(data)
    for va, hx in SIGNATURES.items():
        if at(data, secs, va, 4) != bytes.fromhex(hx):
            raise ValueError(f'steering signature mismatch at {va:#x}')
    for va, target in CALLS.items():
        if ppc_bl_target(at(data, secs, va, 4), va) != target:
            raise ValueError(f'unexpected function call at {va:#x}')
    observed = {}
    for name, (fmt, offset, expected) in CONSTANTS.items():
        size = struct.calcsize(fmt)
        val = struct.unpack(fmt, at(data, secs, SDA2_BASE + offset, size))[0]
        if not math.isclose(val, expected, abs_tol=0, rel_tol=5e-6):
            raise ValueError(f'{name} changed: {val}')
        observed[name] = val
    return {'sha256': digest, 'undercover_wii_function': hex(FUNC),
            'checked_instruction_signatures': len(SIGNATURES),
            'checked_direct_calls': len(CALLS),
            'constants': observed,
            'limitations': ['No PS2 routine identification',
                            'No hardware-device classification',
                            'No claim that this input-only curve predicts full steering output']}


def signed_power(x, exponent):
    return math.copysign(abs(x) ** exponent, x) if x else 0.0


def signed_square(x):
    return x * abs(x)


def early_transformed_input(x, exponent=1.15, deadzone=0.12, use_power=True):
    """Only verified UC Wii early shaping / deadzone, NOT final wheel angle."""
    v = signed_power(x, exponent) if use_power else signed_square(x)
    return v if abs(v) >= deadzone else 0.0


def export_curves(path, constants):
    with path.open('w', newline='', encoding='utf8') as f:
        writer = csv.writer(f)
        writer.writerow(['normalized_input', 'power_path_pre_deadzone',
                         'power_path_post_deadzone', 'square_path_pre_deadzone',
                         'square_path_post_deadzone'])
        for i in range(-20, 21):
            x = i / 20
            writer.writerow([x, signed_power(x, constants['exponent']),
                             early_transformed_input(x, constants['exponent'],
                                                     constants['transformed_input_deadzone'], True),
                             signed_square(x),
                             early_transformed_input(x, constants['exponent'],
                                                     constants['transformed_input_deadzone'], False)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf', type=Path, help='Locally owned NfsMWEuropeEnDuRelease.elf')
    parser.add_argument('--output', type=Path, default=Path('phase32_steering_curve.csv'))
    parser.add_argument('--json', type=Path, default=Path('phase32_steering_evidence.json'))
    args = parser.parse_args()
    try:
        report = verify_elf(args.elf.read_bytes())
        export_curves(args.output, report['constants'])
        args.json.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    except (ValueError, OSError, struct.error) as exc:
        parser.exit(1, f'FAIL: {exc}\n')
    print(f'PASS: {report["checked_instruction_signatures"]} instruction signatures, '
          f'{report["checked_direct_calls"]} calls, {len(CONSTANTS)} constants')
    print('Wrote', args.output, 'and', args.json)


if __name__ == '__main__':
    main()
