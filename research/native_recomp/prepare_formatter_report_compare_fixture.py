#!/usr/bin/env python3
"""Fail-closed private fixture contract for the original post-report-byte compare.

Only the already-authenticated report-byte load and its original immediate
comparison may execute. The next original word is visible to the translator
but protected by a test-only guard at the following slot. This module never
executes translated code or publishes owner instruction words.
"""
import argparse
import struct
from pathlib import Path

from guarded_continuation import GUARD, check_spans
from prepare_formatter_next_report_byte_fixture import render_report_byte
from audit_formatter_report_byte_successor import plan as successor_plan
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


def promote(byte_contract, successor, source):
    """Expand one rooted 118-byte fixture to a guarded 119 compare candidate."""
    # The existing report-byte contract independently authenticates its load,
    # byte value, report-frame offsets, return target and integer successor.
    render_report_byte(byte_contract)
    blocks, info = byte_contract
    root, load, _, _, value, label, comparison, ret = info
    op, reg = comparison >> 26, (comparison >> 16) & 31
    if (not isinstance(source, tuple) or len(source) != 2 or
            type(source[0]) is not int or not 0 <= source[0] < 32 or
            type(source[1]) is not int or not 0 <= source[1] <= 0xffffffff):
        raise ValueError('report compare source provenance')
    if (type(successor) is not int or not 0 <= successor <= 0xffffffff or successor == GUARD):
        raise ValueError('report compare successor')
    if (root & 3 or not 0x80000000 <= root <= 0x817ffff0 or label != root + 4):
        raise ValueError('report compare geometry')
    if (op not in (10, 11) or comparison & 0x00600000):
        raise ValueError('report compare encoding')
    if reg != source[0]:
        raise ValueError('report compare input identity')
    if (type(value) is not int or not 0 <= value <= 255 or
            blocks.get(root) != (load, comparison, GUARD)):
        raise ValueError('report compare predecessor')
    if ret in (root, root+4, root+8, root+12):
        raise ValueError('report compare return')
    expanded = {**blocks, root: (load, comparison, successor, GUARD)}
    check_spans({address: 4 * len(words) for address, words in expanded.items()})
    return expanded, (root, comparison, root+8, successor, source[0], source[1], ret)


def render(contract):
    _, (root, compare, next_pc, next_word, reg, value, ret) = contract
    if next_pc != root+8 or reg >= 32 or value > 0xffffffff or ((compare>>16)&31) != reg:
        raise ValueError('report compare rendering')
    return ('namespace formatter_report_compare_private {\n'
            f'inline constexpr uint32_t root=0x{root:08x}u,compare_pc=0x{root+4:08x}u;\n'
            f'inline constexpr uint32_t compare_word=0x{compare:08x}u,next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u;\n'
            f'inline constexpr uint32_t return_pc=0x{ret:08x}u;\n'
            f'inline constexpr unsigned source_reg={reg}u,source_value=0x{value:08x}u;\n'
            '}\n')


def plan(dol, elf):
    byte, (name, counts, modeled, reason, source) = successor_plan(
        dol, elf, return_input=True, include_byte=True)
    root, load, _, _, _, _, comparison, _ = byte[1]
    size = parse_functions(elf).get(root, 0)
    if not 16 <= size <= 65536 or size % 4:
        raise ValueError('report compare extent')
    actual = exact_words(dol, elf, root, 3)
    if len(actual) != 3 or actual[0] != load or actual[1] != comparison:
        raise ValueError('report compare provenance')
    if (name != 'compare_immediate' or reason != 'supported' or modeled is None or
            counts[0] != 1 or counts[2] != 1 or counts[6] != 1 or
            any(counts[i] for i in (1, 3, 4, 5, 7, 8, 9, 10))):
        raise ValueError('report compare source provenance')
    return promote(byte, actual[2], source)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path)
    parser.add_argument('elf', type=Path)
    args = parser.parse_args()
    safe = {'size', 'report compare extent', 'report compare provenance',
            'report compare boundary', 'report compare successor',
            'report compare geometry', 'report compare encoding',
            'report compare input identity', 'report compare predecessor',
            'report compare return', 'report compare source provenance',
            'successor compare source', 'report byte fixture contract'}
    try:
        if (not 256 <= args.dol.stat().st_size <= MAX_DOL or
                not 52 <= args.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            contract = plan(args.dol.read_bytes(), args.elf.read_bytes())
        render(contract)
    except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error) as error:
        reason = str(error)
        print('FORMATTER_REPORT_COMPARE_FIXTURE verified=0 reason=' +
              (reason.replace(' ', '_') if reason in safe else 'private_input'))
        return 1
    print('FORMATTER_REPORT_COMPARE_FIXTURE verified=1 original_compare=1 source_constant=1 next_original_word=1 stop_guard=1 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
