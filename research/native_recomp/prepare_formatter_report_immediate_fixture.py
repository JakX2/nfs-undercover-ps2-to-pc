#!/usr/bin/env python3
"""Guarded, provenance-only contract for original formatter instruction 121.

The authenticated 120 stack-copy fixture is a mandatory predecessor. Only
PPC addi rD,r0,SIMM (li) with a volatile destination is admitted. No native
execution occurs; the next original word is visible behind a guard.
No original instruction, address or game-derived value is printed.
"""
import argparse
import struct
from pathlib import Path

from audit_formatter_report_copy_successor import inspect as inspect_121
from guarded_continuation import GUARD, check_spans
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

MEM1_BEGIN = 0x80000000
MEM1_END = 0x81800000


def promote(copy, predecessor, compare, following):
    """Advance the existing 120 guard one word; preserve every sibling root."""
    family, name, counts, modeled, reason = inspect_121(
        copy, predecessor, compare)
    if (family, name, modeled, reason) != (
            'integer', 'add_immediate', 1, 'supported') or (
            counts != (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)):
        raise ValueError('report immediate provenance')
    if (type(following) is not int or
            not 0 <= following <= 0xffffffff or following == GUARD):
        raise ValueError('report immediate successor')
    if not isinstance(copy, tuple) or len(copy) != 2 or (
            not isinstance(copy[1], tuple) or len(copy[1]) != 9):
        raise ValueError('report immediate predecessor')
    blocks, fields = copy
    root, copy_pc, copy_word, pc, word, src, copy_dst, offset, ret = fields
    if (type(root) is not int or type(pc) is not int or
            not MEM1_BEGIN <= root < MEM1_END - 24 or
            root & 3 or copy_pc != root + 8 or pc != root + 12 or
            ret in (root, root+4, root+8, root+12, root+16, root+20) or
            blocks.get(root) != (blocks[root][0], blocks[root][1],
                                 copy_word, word, GUARD)):
        raise ValueError('report immediate predecessor')
    op, dst, base = word >> 26, (word >> 21) & 31, (word >> 16) & 31
    if op != 14 or base != 0 or dst not in (0, *range(3, 13)):
        raise ValueError('report immediate encoding')
    value = (word & 0xffff)
    if value & 0x8000:
        value |= 0xffff0000
    out = {**blocks, root: (blocks[root][0], blocks[root][1],
                            copy_word, word, following, GUARD)}
    check_spans({address: 4 * len(words) for address, words in out.items()})
    return out, (root, pc, word, pc + 4, following, dst, value, ret)


def render(contract):
    """Return a *private* C++ header, never send its content to CI logs."""
    if not isinstance(contract, tuple) or len(contract) != 2 or (
            not isinstance(contract[1], tuple) or len(contract[1]) != 8):
        raise ValueError('report immediate rendering')
    _, (root, pc, word, next_pc, following, dst, value, ret) = contract
    if (any(type(x) is not int for x in (
            root, pc, word, next_pc, following, dst, value, ret)) or
            root & 3 or not MEM1_BEGIN <= root < MEM1_END - 24 or
            pc != root + 12 or next_pc != pc + 4 or
            not 0 <= word <= 0xffffffff or
            not 0 <= following <= 0xffffffff or following == GUARD or
            word >> 26 != 14 or (word >> 16) & 31 or
            (word >> 21) & 31 != dst or
            dst not in (0, *range(3, 13)) or
            value != ((word & 0xffff) | (
                0xffff0000 if word & 0x8000 else 0)) or
            ret in (root, root+4, root+8, root+12, root+16, root+20)):
        raise ValueError('report immediate rendering')
    return ('namespace formatter_report_immediate_private {\n'
            f'inline constexpr uint32_t root=0x{root:08x}u,pc=0x{pc:08x}u,word=0x{word:08x}u;\n'
            f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{following:08x}u;\n'
            f'inline constexpr uint32_t return_pc=0x{ret:08x}u;\n'
            f'inline constexpr unsigned destination_reg={dst}u;\n'
            f'inline constexpr uint32_t value=0x{value:08x}u;\n'
            '}\n')


def plan(dol, elf, *, predecessor=None, compare=None, copy=None):
    if predecessor is None:
        predecessor = byte_plan(dol, elf, with_live=True)
    if compare is None:
        compare = compare_plan(dol, elf, predecessor=predecessor)
    if copy is None:
        copy = copy_plan(dol, elf, predecessor=predecessor, compare=compare)
    root = copy[1][0]
    size = parse_functions(elf).get(root, 0)
    if not 24 <= size <= 65536 or size % 4:
        raise ValueError('report immediate extent')
    actual = exact_words(dol, elf, root, 5)
    if len(actual) != 5 or tuple(actual[:4]) != tuple(copy[0][root][:4]):
        raise ValueError('report immediate original')
    return promote(copy, predecessor, compare, actual[4])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path)
    parser.add_argument('elf', type=Path)
    args = parser.parse_args()
    safe = {
        'size', 'report immediate provenance', 'report immediate successor',
        'report immediate predecessor', 'report immediate encoding',
        'report immediate rendering', 'report immediate extent',
        'report immediate original',
    }
    try:
        if (not 256 <= args.dol.stat().st_size <= MAX_DOL or
                not 52 <= args.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            contract = plan(args.dol.read_bytes(), args.elf.read_bytes())
        render(contract)
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            struct.error) as error:
        reason = str(error)
        print('FORMATTER_121_IMMEDIATE_FIXTURE verified=0 reason=' +
              (reason.replace(' ', '_') if reason in safe else 'private_input'))
        return 1
    print('FORMATTER_121_IMMEDIATE_FIXTURE verified=1 previous_120_fixture=1 '
          'instruction_121=add_immediate zero_input=1 volatile_destination=1 '
          'next_guard=1 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
