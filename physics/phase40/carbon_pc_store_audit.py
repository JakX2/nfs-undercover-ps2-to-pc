#!/usr/bin/env python3
"""Phase 40: extract two *known* Carbon PC steering-function store anchors.

Not a general x86 disassembler, pointer analysis, runtime observer, or a
PS2-to-PC field mapping. Supports only Phase 31's SHA-verified executable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from physics.phase31.verify_carbon_pc_steering import (  # noqa: E402
    BYTES, CALLS, at, sections, verify,
)

STEERING_START = 0x006EF540
STEERING_END = 0x006EF819  # exclusive; includes the ret at +0x2D6
ANCHOR_ADDRESSES = (0x006EF7B9, 0x006EF7C0)
GPR = ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi')


def decode_mov_store(code: bytes, address: int) -> dict:
    """Decode precisely MOV r/m32,r32 with ModRM mod=10 and disp32.

    Reject alternate opcodes, SIB addressing and anything lacking a verified
    six-byte boundary. Inputs must be decoded at known instruction addresses.
    """
    if len(code) != 6 or code[0] != 0x89:
        raise ValueError('expected six-byte x86 MOV r/m32,r32 instruction')
    modrm = code[1]
    mod, source, base = modrm >> 6, (modrm >> 3) & 7, modrm & 7
    if mod != 2 or base == 4:  # base=4 would require SIB and >6 bytes
        raise ValueError('not simple ModRM base + signed disp32')
    if base == 5:  # EBP+disp32 is valid when mod=2
        base_name = 'ebp'
    else:
        base_name = GPR[base]
    displacement, = struct.unpack('<i', code[2:])
    return {
        'address': f'0x{address:08X}',
        'relative_steering_address': f'+0x{address - STEERING_START:03X}',
        'instruction': 'mov_dword_ptr_base_plus_disp32_reg',
        'direction': 'write',
        'width_bits': 32,
        'base_register': base_name,
        'source_register': GPR[source],
        'signed_displacement': displacement,
        'syntactic_destination': f'[{base_name}{displacement:+#x}]',
        'field_identity': 'unverified',
    }


def extract_from_verified_image(data: bytes) -> dict:
    """Verify exact source before any structural field-access report."""
    verified = verify(data)  # SHA, PE, cross-function call and byte checks
    mapped = sections(data)
    stores = []
    for pc in ANCHOR_ADDRESSES:
        if not (STEERING_START <= pc and pc + 6 <= STEERING_END):
            raise ValueError('anchor outside verified function bounds')
        evidence = bytes.fromhex(BYTES[pc])
        if len(evidence) != 6:
            raise ValueError('Phase 31 anchor length changed')
        actual = at(data, mapped, pc, 6)
        if actual != evidence:
            raise ValueError(f'anchored instruction mismatch at {pc:#x}')
        stores.append(decode_mov_store(actual, pc))
    return {
        'phase': 40,
        'scope': 'static, exactly pinned Carbon PC x86 steering stores',
        'exe_sha256': verified['sha256'],
        'steering_function_va': verified['function'],
        'phase31_verified_checks': verified['passed_checks'],
        'anchor_count': len(stores),
        'known_steering_store_instructions': stores,
        'source_call_sites_verified': len(CALLS),
        'ps2_field_equivalence_verified': False,
        'semantic_field_names_verified': False,
        'gameplay_patch_created': False,
        'limitations': [
            'These are two anchored x86 store instructions, not every write in this function.',
            'The meaning of the ESI-relative fields and the stored values is unknown.',
            'The prior PS2 +0x188/+0x19C stores are not mapped to these PC offsets.',
            'The verified static stores do not establish which runtime paths execute.',
            'No in-game experiments, hooks, memory reads or binary mutations occur.',
        ],
    }


def save_report(path: Path, output: str, allow_overwrite: bool, source: Path) -> None:
    if path.resolve() == source.resolve():
        raise ValueError('output path must not equal source executable')
    # Exclusive open is the default so original reports cannot be overwritten.
    with path.open('w' if allow_overwrite else 'x', encoding='utf-8') as f:
        f.write(output)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path, help='Exact locally owned Carbon PC NFSC.exe')
    parser.add_argument('--output', type=Path, help='JSON output (stdout by default)')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        data = args.exe.read_bytes()
        result = extract_from_verified_image(data)
        output = json.dumps(result, indent=2) + '\n'
        if args.output:
            save_report(args.output, output, args.overwrite, args.exe)
            print('Phase 40 saved:', args.output)
        else:
            print(output, end='')
        return 0
    except (ValueError, OSError, struct.error) as exc:
        parser.exit(1, f'FAIL (no game modification): {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
