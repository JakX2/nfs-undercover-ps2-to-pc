#!/usr/bin/env python3
"""Guarded original formatter instruction-123 immediate fixture, no execution.

Original 118..122 authentication is mandatory. Admit only the original
123rd PPC addi rD,r0,SIMM with an allowed volatile destination. Carry the
124th original word behind a new stop guard; never publish private bytes.
"""
import argparse
import struct
from pathlib import Path

from audit_formatter_report_signext_successor import inspect as inspect_123
from guarded_continuation import GUARD, check_spans
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_formatter_report_immediate_fixture import plan as immediate_plan
from prepare_formatter_report_signext_fixture import plan as signext_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

MEM1_BEGIN = 0x80000000
MEM1_END = 0x81800000
EXPECTED_COUNTS = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)


def zero_immediate(word):
    if type(word) is not int or not 0 <= word <= 0xffffffff:
        raise ValueError('report second immediate encoding')
    op, dst, ra = word >> 26, (word >> 21) & 31, (word >> 16) & 31
    if op != 14 or ra != 0 or dst not in (0, *range(3, 13)):
        raise ValueError('report second immediate encoding')
    imm = word & 0xffff
    return dst, imm | (0xffff0000 if imm & 0x8000 else 0)


def promote(signext, immediate, copy, predecessor, compare, following):
    """Advance exactly one authenticated word while preserving prior guards."""
    result = inspect_123(signext, immediate, copy, predecessor, compare)
    if result != (
            'integer', 'add_immediate', EXPECTED_COUNTS, 1, 'supported'):
        raise ValueError('report second immediate provenance')
    if (type(following) is not int or
            not 0 <= following <= 0xffffffff or following == GUARD):
        raise ValueError('report second immediate successor')
    if (not isinstance(signext, tuple) or len(signext) != 2 or
            not isinstance(signext[0], dict) or
            not isinstance(signext[1], tuple) or len(signext[1]) != 9):
        raise ValueError('report second immediate predecessor')
    blocks, info = signext
    root, oldpc, oldword, pc, word, oldreg, before, after, ret = info
    if (any(type(x) is not int for x in info) or root & 3 or
            not MEM1_BEGIN <= root < MEM1_END - 32 or
            oldpc != root + 16 or pc != root + 20 or
            root not in blocks or len(blocks[root]) != 7 or
            blocks[root][4:] != (oldword, word, GUARD) or
            ret in tuple(root + n for n in range(0, 32, 4))):
        raise ValueError('report second immediate predecessor')
    dst, value = zero_immediate(word)
    out = {**blocks, root: blocks[root][:-1] + (following, GUARD)}
    check_spans({address: 4 * len(words) for address, words in out.items()})
    return out, (root, pc, word, pc + 4, following, dst, value, ret)


def render(contract):
    """Create the owner-only C++ declaration after checking its whole guard."""
    if (not isinstance(contract, tuple) or len(contract) != 2 or
            not isinstance(contract[1], tuple) or len(contract[1]) != 8):
        raise ValueError('report second immediate rendering')
    blocks, info = contract
    root, pc, word, next_pc, following, dst, value, ret = info
    if (not isinstance(blocks, dict) or root not in blocks or
            not isinstance(blocks[root], tuple) or len(blocks[root]) != 8 or
            blocks[root][5:] != (word, following, GUARD) or
            any(type(x) is not int for x in info) or root & 3 or
            not MEM1_BEGIN <= root < MEM1_END - 32 or
            pc != root + 20 or next_pc != root + 24 or
            following == GUARD or not 0 <= following <= 0xffffffff or
            zero_immediate(word) != (dst, value) or
            ret in tuple(root + n for n in range(0, 32, 4))):
        raise ValueError('report second immediate rendering')
    try:
        check_spans({address: 4 * len(words) for address, words in blocks.items()})
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError('report second immediate rendering') from error
    return (
        'namespace formatter_report_second_immediate_private {\n'
        f'inline constexpr uint32_t root=0x{root:08x}u,pc=0x{pc:08x}u,word=0x{word:08x}u;\n'
        f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{following:08x}u;\n'
        f'inline constexpr uint32_t return_pc=0x{ret:08x}u;\n'
        f'inline constexpr unsigned destination_reg={dst}u;\n'
        f'inline constexpr uint32_t value=0x{value:08x}u;\n'
        '}\n')


def plan(dol, elf, *, predecessor=None, compare=None, copy=None,
         immediate=None, signext=None):
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
    root = signext[1][0]
    size = parse_functions(elf).get(root, 0)
    if not 28 <= size <= 65536 or size % 4:
        raise ValueError('report second immediate extent')
    actual = exact_words(dol, elf, root, 7)
    if (len(actual) != 7 or
            tuple(actual[:6]) != tuple(signext[0][root][:6])):
        raise ValueError('report second immediate original')
    return promote(
        signext, immediate, copy, predecessor, compare, actual[6])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path)
    parser.add_argument('elf', type=Path)
    args = parser.parse_args()
    safe = {
        'size', 'report second immediate provenance',
        'report second immediate successor', 'report second immediate predecessor',
        'report second immediate encoding', 'report second immediate rendering',
        'report second immediate extent', 'report second immediate original',
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
        print('FORMATTER_123_IMMEDIATE_FIXTURE verified=0 reason=' +
              (reason.replace(' ', '_') if reason in safe else 'private_input'))
        return 1
    print('FORMATTER_123_IMMEDIATE_FIXTURE verified=1 previous_122_fixture=1 '
          'instruction_123=add_immediate zero_input=1 volatile_destination=1 '
          'next_guard=1 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
