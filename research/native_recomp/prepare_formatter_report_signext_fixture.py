#!/usr/bin/env python3
"""Private, fail-closed fixture for original formatter instruction 122.

Replays authenticated byte-load/compare/stack-copy/zero-input-immediate
provenance, then admits only non-record PPC extsb rA,rS where rA == rS
and the 121st instruction proved the source's exact 32-bit value.
No original PPC word, address, register value, or generated C++ is logged.
This module is a *fixture*, not evidence of native execution.
"""
import argparse
import struct
from pathlib import Path

from audit_formatter_report_immediate_successor import inspect as inspect_122
from guarded_continuation import GUARD, check_spans
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_formatter_report_stack_copy_fixture import plan as copy_plan
from prepare_formatter_report_immediate_fixture import plan as immediate_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

MEM1_BEGIN = 0x80000000
MEM1_END = 0x81800000
EXPECTED_COUNTS = (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1)


def encoding(word):
    """Decode only non-record extsb with a single aliased volatile GPR."""
    if type(word) is not int or not 0 <= word <= 0xffffffff:
        raise ValueError('report signext encoding')
    rs = (word >> 21) & 31
    ra = (word >> 16) & 31
    if (word >> 26 != 31 or (word >> 1) & 1023 != 954 or
            (word >> 11) & 31 or word & 1 or rs != ra or
            ra not in (0, *range(3, 13))):
        raise ValueError('report signext encoding')
    return ra


def sign_extend_byte(value):
    """Return the exact unsigned 32-bit PPC extsb result."""
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('report signext value')
    low = value & 0xff
    return (low | 0xffffff00) if low & 0x80 else low


def promote(immediate, copy, predecessor, compare, following):
    """Move the private fifth-slot guard, preserving sibling blocks."""
    family, name, counts, modeled, reason = inspect_122(
        immediate, copy, predecessor, compare)
    if (family, name, counts, modeled, reason) != (
            'integer', 'sign_extend_byte', EXPECTED_COUNTS, 1, 'supported'):
        raise ValueError('report signext provenance')
    if type(following) is not int or not 0 <= following <= 0xffffffff or following == GUARD:
        raise ValueError('report signext successor')
    if (not isinstance(immediate, tuple) or len(immediate) != 2 or
            not isinstance(immediate[0], dict) or
            not isinstance(immediate[1], tuple) or len(immediate[1]) != 8):
        raise ValueError('report signext predecessor')
    blocks, fields = immediate
    root, pc_121, word_121, pc, word, prior_dst, prior_value, ret = fields
    if (any(type(x) is not int for x in fields) or
            root & 3 or not MEM1_BEGIN <= root < MEM1_END - 28 or
            pc_121 != root + 12 or pc != root + 16 or
            blocks.get(root) is None or
            len(blocks[root]) != 6 or blocks[root][-1] != GUARD or
            blocks[root][3] != word_121 or blocks[root][4] != word or
            ret in tuple(root + n for n in range(0, 28, 4))):
        raise ValueError('report signext predecessor')
    dest = encoding(word)
    # The source need not be the destination of 121's li. Replay the
    # authenticated state, rather than inventing a dependence on that li.
    try:
        byte, registers, saved_mask = predecessor
        live = list(registers)
        load, byte_value = byte[1][1], byte[1][4]
        live[(load >> 21) & 31] = ('const', byte_value)
        after_compare, _ = step(byte[1][6], tuple(live), saved_mask=saved_mask)
        after_copy, _ = step(copy[1][2], after_compare,
                             saved_mask=saved_mask, allow_stack_copy=True)
        after_121, _ = step(word_121, after_copy, saved_mask=saved_mask)
        source = after_121[dest]
        if (not isinstance(source, tuple) or len(source) != 2 or
                source[0] != 'const' or type(source[1]) is not int or
                not 0 <= source[1] <= 0xffffffff):
            raise ValueError('report signext input')
        before = source[1]
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError('report signext input') from error
    value = sign_extend_byte(before)
    out = {**blocks, root: blocks[root][:-1] + (following, GUARD)}
    check_spans({address: 4 * len(words) for address, words in out.items()})
    return out, (root, pc, word, pc + 4, following, dest, before, value, ret)


def render(contract):
    """Generate an owner-private declaration for the native witness."""
    if (not isinstance(contract, tuple) or len(contract) != 2 or
            not isinstance(contract[1], tuple) or len(contract[1]) != 9):
        raise ValueError('report signext rendering')
    blocks, fields = contract
    root, pc, word, next_pc, following, reg, before, after, ret = fields
    if (not isinstance(blocks, dict) or root not in blocks or
            not isinstance(blocks[root], tuple) or len(blocks[root]) != 7 or
            blocks[root][4:] != (word, following, GUARD)):
        raise ValueError('report signext rendering')
    try:
        check_spans({address: 4 * len(words) for address, words in blocks.items()})
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError('report signext rendering') from error
    if (any(type(x) is not int for x in fields) or
            root & 3 or not MEM1_BEGIN <= root < MEM1_END - 28 or
            pc != root + 16 or next_pc != root + 20 or
            following == GUARD or not 0 <= following <= 0xffffffff or
            encoding(word) != reg or sign_extend_byte(before) != after or
            ret in tuple(root + n for n in range(0, 28, 4))):
        raise ValueError('report signext rendering')
    return (
        'namespace formatter_report_signext_private {\n'
        f'inline constexpr uint32_t root=0x{root:08x}u,pc=0x{pc:08x}u,word=0x{word:08x}u;\n'
        f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{following:08x}u;\n'
        f'inline constexpr uint32_t return_pc=0x{ret:08x}u;\n'
        f'inline constexpr unsigned destination_reg={reg}u;\n'
        f'inline constexpr uint32_t input_value=0x{before:08x}u,output_value=0x{after:08x}u;\n'
        '}\n')


def plan(dol, elf, *, predecessor=None, compare=None, copy=None, immediate=None):
    if predecessor is None:
        predecessor = byte_plan(dol, elf, with_live=True)
    if compare is None:
        compare = compare_plan(dol, elf, predecessor=predecessor)
    if copy is None:
        copy = copy_plan(dol, elf, predecessor=predecessor, compare=compare)
    if immediate is None:
        immediate = immediate_plan(
            dol, elf, predecessor=predecessor, compare=compare, copy=copy)
    root = immediate[1][0]
    size = parse_functions(elf).get(root, 0)
    if not 24 <= size <= 65536 or size % 4:
        raise ValueError('report signext extent')
    actual = exact_words(dol, elf, root, 6)
    if (len(actual) != 6 or
            tuple(actual[:5]) != tuple(immediate[0][root][:5])):
        raise ValueError('report signext original')
    return promote(immediate, copy, predecessor, compare, actual[5])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path)
    parser.add_argument('elf', type=Path)
    args = parser.parse_args()
    safe = {
        'size', 'report signext provenance', 'report signext successor',
        'report signext predecessor', 'report signext encoding',
        'report signext input', 'report signext value',
        'report signext rendering', 'report signext extent',
        'report signext original',
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
        print('FORMATTER_122_SIGNEXT_FIXTURE verified=0 reason=' +
              (reason.replace(' ', '_') if reason in safe else 'private_input'))
        return 1
    print('FORMATTER_122_SIGNEXT_FIXTURE verified=1 previous_121_fixture=1 '
          'instruction_122=sign_extend_byte constant_input=1 '
          'alias=1 nonrecord=1 next_guard=1 original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
