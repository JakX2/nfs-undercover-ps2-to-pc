#!/usr/bin/env python3
"""Phase 42: read-only ESI-relative memory-access census for Carbon PC steering.

Only exact Phase31/40-verified game versions qualify. Instruction boundaries
come from Phase41 GNU objdump. This is syntax, NOT recovered C++ field identity.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from physics.phase40.carbon_pc_store_audit import (  # noqa: E402
    ANCHOR_ADDRESSES, BYTES, STEERING_START, STEERING_END, at,
    extract_from_verified_image, save_report, sections,
)
from physics.phase41.carbon_pc_register_trace import (  # noqa: E402
    disassemble, split_operands,
)

# Accept only a single 32-bit base register with an optional *constant*
# displacement. Scaled-index and segmented forms must not be silently mapped
# to one field. On this target, objdump uses Intel uppercase PTR widths.
MEMORY_OPERAND = re.compile(
    r"^(?:(?:BYTE|WORD|DWORD|QWORD|TBYTE|XMMWORD|YMMWORD) PTR )?"
    r"\[([^\[\]]+)\]$", re.IGNORECASE
)
BARE_32_REGS = frozenset(('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'))
NON_DEREFERENCE = frozenset(('lea',))
READ_DEST = frozenset(('cmp', 'test', 'push', 'call', 'jmp',
                       'movsx', 'movzx', 'fld', 'fld1', 'fldz',
                       'fadd', 'fsub', 'fmul', 'fdiv', 'fcom',
                       'fcomp', 'fucom', 'fucomp'))
WRITE_DEST = frozenset(('mov', 'fst', 'fstp', 'fist', 'fistp', 'pop', 'seta',
                        'sete', 'setne', 'setb', 'setg', 'setl', 'setge',
                        'setle', 'setbe', 'setae'))
READ_WRITE_DEST = frozenset(('add', 'sub', 'adc', 'sbb', 'xor', 'and', 'or',
                             'inc', 'dec', 'neg', 'not', 'xchg',
                             'shl', 'shr', 'sar', 'rol', 'ror', 'bts', 'btr', 'btc'))
READ_SOURCE = frozenset(('mov', 'movsx', 'movzx', 'cmp', 'test', 'add', 'sub',
                         'adc', 'sbb', 'xor', 'and', 'or', 'imul', 'xchg',
                         'shl', 'shr', 'sar', 'rol', 'ror'))


def parse_mem_operand(operand: str) -> dict | None:
    """Return conservative structural addressing, or None for non-memory.

    Complex expressions remain visible with kind=complex, never reduced to a
    fake ESI-relative object displacement. Malformed signs are rejected.
    """
    operand = operand.strip()
    match = MEMORY_OPERAND.fullmatch(operand)
    if not match:
        return None
    expression = match.group(1).replace(' ', '').lower()
    if '*' in expression or ':' in expression:
        return {'kind': 'complex', 'expression': expression}
    match = re.fullmatch(r"([a-z][a-z0-9]*)(?:(\+|-)(0x[0-9a-f]+|[0-9]+))?",
                         expression)
    if not match or match.group(1) not in BARE_32_REGS:
        return {'kind': 'complex', 'expression': expression}
    base = match.group(1)
    raw = match.group(3)
    amount = (int(raw, 16) if raw and raw.startswith('0x') else
              int(raw, 10) if raw else 0)
    if amount > 0x7fffffff:
        return {'kind': 'complex', 'expression': expression}
    displacement = -amount if match.group(2) == '-' else amount
    return {'kind': 'simple', 'base_register': base,
            'signed_displacement': displacement}


def access_direction(mnemonic: str, operand_index: int,
                     operand_count: int) -> str:
    """Only return read/write on a constrained list of instruction families.

    Unknown remains unknown and is explicitly counted; LEA is not a read.
    """
    m = mnemonic.lower()
    if m in NON_DEREFERENCE:
        return 'address_only_no_memory_access'
    if operand_index == 0:
        if m in READ_WRITE_DEST:
            return 'read_write'
        if m in WRITE_DEST:
            return 'write'
        if m in READ_DEST:
            return 'read'
        return 'unknown'
    if operand_count == 2 and operand_index == 1 and m in READ_SOURCE:
        return 'read'
    return 'unknown'


def find_accesses(instructions: list[dict]) -> dict:
    """Enumerate only text-disassembled explicit ESI-base operands.

    No memory access through another pointer register is called an ESI field.
    No branch or path analysis is attempted. Report unknown cases.
    """
    stores = set(ANCHOR_ADDRESSES)
    rows, complex_esi, unknown_memory_forms = [], [], []
    for ins in instructions:
        operands = split_operands(ins['operands'])
        for index, operand in enumerate(operands):
            parsed = parse_mem_operand(operand)
            if parsed is None:
                if '[' in operand or ']' in operand:
                    unknown_memory_forms.append({
                        'pc': f"0x{ins['pc']:08X}",
                        'mnemonic': ins['mnemonic'],
                        'operand_index': index, 'expression': operand,
                    })
                continue
            direction = access_direction(ins['mnemonic'], index, len(operands))
            if parsed['kind'] == 'complex':
                # Any occurrence of esi in a complex indexed/segmented
                # expression is an unresolved candidate, not a field map.
                if re.search(r'\besi\b', parsed['expression']):
                    complex_esi.append({
                        'pc': f"0x{ins['pc']:08X}",
                        'mnemonic': ins['mnemonic'],
                        'operand_index': index, 'direction': direction,
                        'expression': parsed['expression'],
                    })
                continue
            if parsed['base_register'] != 'esi':
                continue
            if direction == 'address_only_no_memory_access':
                continue
            rows.append({
                'pc': f"0x{ins['pc']:08X}",
                'relative_steering_pc': f"+0x{ins['pc'] - STEERING_START:03X}",
                'mnemonic': ins['mnemonic'],
                'operand_index': index, 'direction': direction,
                'base_register': 'esi',
                'signed_displacement': parsed['signed_displacement'],
                'known_phase40_anchor': ins['pc'] in stores,
                'semantic_field_identity': 'unknown',
            })
    groups = defaultdict(list)
    for row in rows:
        groups[row['signed_displacement']].append(row)
    return {
        'simple_esi_access_count': len(rows),
        'complex_esi_operand_count': len(complex_esi),
        'unknown_memory_operand_form_count': len(unknown_memory_forms),
        'simple_esi_accesses': rows,
        'by_displacement': [{
            'signed_displacement': disp,
            'static_instruction_count': len(accesses),
            'directions': sorted(set(x['direction'] for x in accesses)),
            'pcs': [x['pc'] for x in accesses],
            'contains_phase40_anchor': any(x['known_phase40_anchor'] for x in accesses),
        } for disp, accesses in sorted(groups.items())],
        'complex_esi_operands': complex_esi,
        'unparsed_memory_operand_forms': unknown_memory_forms,
    }


def audit_verified_pc(data: bytes) -> dict:
    """Verify supported NFSC.exe fully before using GNU disassembly."""
    verified = extract_from_verified_image(data)
    mapped = sections(data)
    code = at(data, mapped, STEERING_START, STEERING_END - STEERING_START)
    instructions = disassemble(code, STEERING_START)
    index = {ins['pc']: ins for ins in instructions}
    for address in ANCHOR_ADDRESSES:
        ins = index.get(address)
        if ins is None or ins['bytes'] != bytes.fromhex(BYTES[address]):
            raise ValueError(f'Phase 40 anchor not independently decoded at {address:#x}')
    results = find_accesses(instructions)
    for pc, expected_disp in zip(ANCHOR_ADDRESSES, (0x104, 0x118)):
        hits = [r for r in results['simple_esi_accesses']
                if int(r['pc'], 16) == pc and r['signed_displacement'] == expected_disp
                and r['direction'] == 'write']
        if len(hits) != 1:
            raise ValueError(f'Phase 40 anchor absent from ESI write inventory at {pc:#x}')
    return {
        'phase': 42,
        'source_sha256': verified['exe_sha256'],
        'steering_function_va': verified['steering_function_va'],
        'phase31_verified_checks': verified['phase31_verified_checks'],
        'disassembler': 'GNU objdump (32-bit Intel syntax)',
        'instructions_decoded': len(instructions),
        **results,
        'semantic_field_equivalence_established': False,
        'runtime_values_observed': False,
        'gameplay_patch_created': False,
        'limitations': [
            'Static explicit operands only; ESI may change between instructions.',
            'Identical offsets do not imply one object on all code paths.',
            'Complex or indexed addresses are not attributed to simple ESI fields.',
            'Unknown direction is not silently classified as a read or write.',
            'Indirect addresses through registers derived from ESI are not tracked.',
            'No PS2-to-PC offsets or field meanings are established.',
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path, help='Exact supported locally owned NFSC.exe')
    parser.add_argument('--output', type=Path, help='JSON output path (stdout by default)')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = audit_verified_pc(args.exe.read_bytes())
        rendered = json.dumps(result, indent=2) + '\n'
        if args.output:
            save_report(args.output, rendered, args.overwrite, args.exe)
            print('Phase 42 report saved:', args.output)
        else:
            print(rendered, end='')
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f'FAIL (game untouched): {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
