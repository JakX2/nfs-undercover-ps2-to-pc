#!/usr/bin/env python3
"""Private, guarded fixture admission for original instruction 120.

Only a non-record PPC OR of identical stack-derived operands is admitted.
The next original word is visible for translation but may not execute.
Neither the original words nor guest addresses are printed by this module.
"""
import argparse
import struct
from pathlib import Path

from audit_formatter_report_compare_successor import inspect
from guarded_continuation import GUARD, check_spans
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_formatter_caller_integer_contract import step
from prepare_formatter_next_entry_report_byte_contract import plan as byte_plan
from prepare_formatter_report_compare_fixture import plan as compare_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope


def promote(compare, predecessor, next_word):
    """Move the 119 guard exactly one original instruction forward."""
    family, name, counts, modeled, reason = inspect(compare, predecessor)
    if (family, name, modeled, reason) != ('integer', 'or', 1, 'supported') or (
            counts != (1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0)):
        raise ValueError('report copy provenance')
    if type(next_word) is not int or not 0 <= next_word <= 0xffffffff or next_word == GUARD:
        raise ValueError('report copy successor')
    blocks, info = compare
    root, cmp, pc, word, _, _, ret = info
    if pc != root + 8 or blocks.get(root) != (blocks[root][0], cmp, word, GUARD):
        raise ValueError('report copy predecessor')
    if len(predecessor) != 3:
        raise ValueError('report copy provenance')
    byte, registers, mask = predecessor
    if byte[1][0] != root or byte[1][6] != cmp or byte[1][7] != ret:
        raise ValueError('report copy predecessor')
    after = list(registers)
    load = byte[1][1]
    after[(load >> 21) & 31] = ('const', byte[1][4])
    after, _ = step(cmp, after, saved_mask=mask)
    rs, ra, rb = (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
    if (word >> 26 != 31 or (word >> 1) & 1023 != 444 or word & 1 or
            rs != rb or ra == rs or after[rs][0] != 'stack' or
            after[1][0] != 'stack' or type(after[rs][1]) is not int or
            type(after[1][1]) is not int):
        raise ValueError('report copy encoding')
    offset = after[rs][1] - after[1][1]
    if not -0x01800000 < offset < 0x01800000:
        raise ValueError('report copy range')
    result, numeric_inputs = step(word, after, saved_mask=mask, allow_stack_copy=True)
    if numeric_inputs or result[ra] != after[rs] or any(
            result[r] != after[r] for r in range(32) if r != ra):
        raise ValueError('report copy effects')
    out = {**blocks, root: (blocks[root][0], cmp, word, next_word, GUARD)}
    check_spans({address: 4 * len(words) for address, words in out.items()})
    return out, (root, pc, word, pc + 4, next_word, rs, ra, offset, ret)


def render(contract):
    _, (root, pc, word, next_pc, next_word, rs, ra, offset, ret) = contract
    if (root & 3 or pc != root + 8 or next_pc != pc + 4 or
            rs >= 32 or ra >= 32 or rs == ra or
            word >> 26 != 31 or (word >> 1) & 1023 != 444 or
            word & 1 or (word >> 21) & 31 != rs or
            (word >> 16) & 31 != ra or (word >> 11) & 31 != rs or
            not -0x01800000 < offset < 0x01800000 or next_word == GUARD):
        raise ValueError('report copy rendering')
    return ('namespace formatter_report_copy_private {\n'
            f'inline constexpr uint32_t root=0x{root:08x}u,pc=0x{pc:08x}u,word=0x{word:08x}u;\n'
            f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u,return_pc=0x{ret:08x}u;\n'
            f'inline constexpr unsigned source_reg={rs}u,destination_reg={ra}u;\n'
            f'inline constexpr int32_t source_offset={offset};\n'
            '}\n')


def plan(dol, elf, *, predecessor=None, compare=None):
    if predecessor is None:
        predecessor = byte_plan(dol, elf, with_live=True)
    if compare is None:
        compare = compare_plan(dol, elf, predecessor=predecessor)
    root = compare[1][0]
    size = parse_functions(elf).get(root, 0)
    if not 20 <= size <= 65536 or size % 4:
        raise ValueError('report copy extent')
    actual = exact_words(dol, elf, root, 4)
    if tuple(actual[:3]) != tuple(compare[0][root][:3]):
        raise ValueError('report copy original')
    return promote(compare, predecessor, actual[3])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dol', type=Path)
    parser.add_argument('elf', type=Path)
    args = parser.parse_args()
    safe = {'size', 'report copy provenance', 'report copy successor',
            'report copy predecessor', 'report copy encoding', 'report copy range',
            'report copy effects', 'report copy extent', 'report copy original',
            'report copy rendering'}
    try:
        if (not 256 <= args.dol.stat().st_size <= MAX_DOL or
                not 52 <= args.elf.stat().st_size <= 64 * 1024 * 1024):
            raise ValueError('size')
        with plan_cache_scope():
            contract = plan(args.dol.read_bytes(), args.elf.read_bytes())
        render(contract)
    except (OSError, ValueError, TypeError, KeyError, IndexError, struct.error) as error:
        msg = str(error)
        print('FORMATTER_120_COPY_FIXTURE verified=0 reason=' +
              (msg.replace(' ', '_') if msg in safe else 'private_input'))
        return 1
    print('FORMATTER_120_COPY_FIXTURE verified=1 original_119=1 '
          'instruction_120=or stack_source=1 guarded_successor=1 '
          'original_execution=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
