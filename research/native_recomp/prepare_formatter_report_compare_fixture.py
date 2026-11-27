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
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


def promote(byte_contract, successor):
    """Expand one rooted 118-byte fixture to a guarded 119 compare candidate."""
    # The existing report-byte contract independently authenticates its load,
    # byte value, report-frame offsets, return target and integer successor.
    render_report_byte(byte_contract)
    blocks, info = byte_contract
    root, load, _, _, value, label, comparison, ret = info
    op, reg = comparison >> 26, (comparison >> 16) & 31
    rt = (load >> 21) & 31
    if (type(successor) is not int or not 0 <= successor <= 0xffffffff or
            successor == GUARD or root & 3 or
            not 0x80000000 <= root <= 0x817ffff0 or
            label != root + 4 or
            op not in (10, 11) or comparison & 0x00600000 or
            reg != rt or not 0 <= value <= 255 or
            ret in (root, root+4, root+8, root+12) or
            blocks.get(root) != (load, comparison, GUARD)):
        raise ValueError('report compare boundary')
    expanded = {**blocks, root: (load, comparison, successor, GUARD)}
    check_spans({address: 4 * len(words) for address, words in expanded.items()})
    return expanded, (root, comparison, root+8, successor, rt, value, ret)


def render(contract):
    _, (root, compare, next_pc, next_word, reg, value, ret) = contract
    if next_pc != root+8 or reg >= 32 or value > 255:
        raise ValueError('report compare rendering')
    return ('namespace formatter_report_compare_private {\n'
            f'inline constexpr uint32_t root=0x{root:08x}u,compare_pc=0x{root+4:08x}u;\n'
            f'inline constexpr uint32_t compare_word=0x{compare:08x}u,next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u;\n'
            f'inline constexpr uint32_t return_pc=0x{ret:08x}u;\n'
            f'inline constexpr unsigned source_reg={reg}u,source_byte={value}u;\n'
            '}\n')


def plan(dol, elf):
    byte = byte_plan(dol, elf)
    root, load, _, _, _, _, comparison, _ = byte[1]
    size = parse_functions(elf).get(root, 0)
    if not 16 <= size <= 65536 or size % 4:
        raise ValueError('report compare extent')
    actual = exact_words(dol, elf, root, 3)
    if len(actual) != 3 or actual[0] != load or actual[1] != comparison:
        raise ValueError('report compare provenance')
    return promote(byte, actual[2])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path)
    parser.add_argument('elf', type=Path)
    args = parser.parse_args()
    safe = {'size', 'report compare extent', 'report compare provenance',
            'report compare boundary', 'report byte fixture contract'}
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
    print('FORMATTER_REPORT_COMPARE_FIXTURE verified=1 original_compare=1 source_byte=1 next_original_word=1 stop_guard=1 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
