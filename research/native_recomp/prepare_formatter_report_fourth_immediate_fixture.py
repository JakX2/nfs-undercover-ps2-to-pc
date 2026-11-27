#!/usr/bin/env python3
"""Guarded, provenance-only contract for original formatter instruction 125.

Reconstruct the original 118–124 chain and admit only original 125 PPC
addi rD,r0,SIMM with an allowed volatile destination. Carry original 126
behind a private synthetic syscall guard. The original DOL, operands,
instruction words, and emitted C++ stay owner-private. No game execution.
"""
import argparse
import struct
from pathlib import Path

from audit_formatter_report_third_immediate_successor import inspect as inspect_125
from guarded_continuation import GUARD, check_spans
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_formatter_report_immediate_fixture import plan as immediate_plan
from prepare_formatter_report_signext_fixture import plan as signext_plan
from prepare_formatter_report_post_signext_immediate_fixture import plan as second_immediate_plan
from prepare_formatter_report_third_immediate_fixture import (
    plan as third_immediate_plan, zero_immediate,
)
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

MEM1_BEGIN = 0x80000000
MEM1_END = 0x81800000
EXPECTED_COUNTS = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)


def promote(third, second, signext, immediate, copy, predecessor, compare, following):
    """Advance exactly one authenticated word; preserve all sibling roots."""
    if inspect_125(third, second, signext, immediate, copy, predecessor, compare) != (
            'integer', 'add_immediate', EXPECTED_COUNTS, 1, 'supported'):
        raise ValueError('report fourth immediate provenance')
    if (type(following) is not int or
            not 0 <= following <= 0xffffffff or following == GUARD):
        raise ValueError('report fourth immediate successor')
    if (not isinstance(third, tuple) or len(third) != 2 or
            not isinstance(third[0], dict) or
            not isinstance(third[1], tuple) or len(third[1]) != 8):
        raise ValueError('report fourth immediate predecessor')
    blocks, fields = third
    root, oldpc, oldword, pc, word, olddst, oldvalue, ret = fields
    if (any(type(x) is not int for x in fields) or root & 3 or
            not MEM1_BEGIN <= root < MEM1_END - 40 or
            oldpc != root + 24 or pc != root + 28 or
            root not in blocks or not isinstance(blocks[root], tuple) or
            len(blocks[root]) != 9 or
            blocks[root][6:] != (oldword, word, GUARD) or
            ret in tuple(root + n for n in range(0, 40, 4))):
        raise ValueError('report fourth immediate predecessor')
    dst, value = zero_immediate(word)
    out = {**blocks, root: blocks[root][:-1] + (following, GUARD)}
    check_spans({address: 4 * len(words) for address, words in out.items()})
    return out, (root, pc, word, pc + 4, following, dst, value, ret)


def render(contract):
    """Produce an owner-private C++ declaration, never public log bytes."""
    if (not isinstance(contract, tuple) or len(contract) != 2 or
            not isinstance(contract[1], tuple) or len(contract[1]) != 8):
        raise ValueError('report fourth immediate rendering')
    blocks, fields = contract
    root, pc, word, next_pc, following, dst, value, ret = fields
    if (not isinstance(blocks, dict) or root not in blocks or
            not isinstance(blocks[root], tuple) or len(blocks[root]) != 10 or
            blocks[root][7:] != (word, following, GUARD) or
            any(type(x) is not int for x in fields) or root & 3 or
            not MEM1_BEGIN <= root < MEM1_END - 40 or
            pc != root + 28 or next_pc != root + 32 or
            type(following) is not int or not 0 <= following <= 0xffffffff or
            following == GUARD or zero_immediate(word) != (dst, value) or
            ret in tuple(root + n for n in range(0, 40, 4))):
        raise ValueError('report fourth immediate rendering')
    try:
        check_spans({address: 4 * len(words) for address, words in blocks.items()})
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError('report fourth immediate rendering') from error
    return (
        'namespace formatter_report_fourth_immediate_private {\n'
        f'inline constexpr uint32_t root=0x{root:08x}u,pc=0x{pc:08x}u,word=0x{word:08x}u;\n'
        f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{following:08x}u;\n'
        f'inline constexpr uint32_t return_pc=0x{ret:08x}u;\n'
        f'inline constexpr unsigned destination_reg={dst}u;\n'
        f'inline constexpr uint32_t value=0x{value:08x}u;\n'
        '}\n')


def plan(dol, elf, *, predecessor=None, compare=None, copy=None,
         immediate=None, signext=None, second=None, third=None):
    if predecessor is None:
        predecessor = byte_plan(dol, elf, with_live=True)
    if compare is None:
        compare = compare_plan(dol, elf, predecessor=predecessor)
    if copy is None:
        copy = copy_plan(dol, elf, predecessor=predecessor, compare=compare)
    if immediate is None:
        immediate = immediate_plan(
            dol, elf, predecessor=predecessor, compare=compare, copy=copy)
    if signext is None:
        signext = signext_plan(
            dol, elf, predecessor=predecessor, compare=compare,
            copy=copy, immediate=immediate)
    if second is None:
        second = second_immediate_plan(
            dol, elf, predecessor=predecessor, compare=compare,
            copy=copy, immediate=immediate, signext=signext)
    if third is None:
        third = third_immediate_plan(
            dol, elf, predecessor=predecessor, compare=compare,
            copy=copy, immediate=immediate, signext=signext, second=second)
    root = third[1][0]
    size = parse_functions(elf).get(root, 0)
    if not 36 <= size <= 65536 or size % 4:
        raise ValueError('report fourth immediate extent')
    actual = exact_words(dol, elf, root, 9)
    if (len(actual) != 9 or
            tuple(actual[:8]) != tuple(third[0][root][:8])):
        raise ValueError('report fourth immediate original')
    return promote(
        third, second, signext, immediate, copy, predecessor, compare, actual[8])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path)
    parser.add_argument('elf', type=Path)
    args = parser.parse_args()
    safe = {
        'size', 'report fourth immediate provenance',
        'report fourth immediate successor', 'report fourth immediate predecessor',
        'report fourth immediate rendering', 'report fourth immediate extent',
        'report fourth immediate original', 'report second immediate encoding',
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
        msg = str(error)
        print('FORMATTER_125_IMMEDIATE_FIXTURE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    print('FORMATTER_125_IMMEDIATE_FIXTURE verified=1 previous_124_fixture=1 '
          'instruction_125=add_immediate zero_input=1 volatile_destination=1 '
          'next_guard=1 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
