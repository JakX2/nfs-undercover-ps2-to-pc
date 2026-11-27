#!/usr/bin/env python3
"""Guarded fixture expansion for one original callee report-frame byte load.

Pure source helper: never stages private originals, executes the game, or
writes translated original instruction words into the repository.
"""
from guarded_continuation import GUARD, check_spans
from audit_formatter_partial_copy import boundary_shape


def render_report_byte(contract):
    """Produce private runner constants only after exact public guards."""
    _, info = contract
    if len(info) != 8:
        raise ValueError('report byte fixture shape')
    root, word, relative, report_offset, value, next_pc, next_word, _ = info
    op, rt, xo = word >> 26, (word >> 21) & 31, (word >> 1) & 1023
    if (root & 3 or next_pc != root + 4 or
            not (op == 34 or op == 31 and xo == 87 and not word & 1) or
            rt not in (0, *range(3, 13)) or
            type(relative) is not int or not 704 <= relative <= 2048 or
            type(report_offset) is not int or not 8 <= report_offset <= 512 or
            type(value) is not int or not 0 <= value <= 255 or
            next_word == GUARD or boundary_shape(next_word) != 'integer'):
        raise ValueError('report byte fixture contract')
    return ('namespace formatter_next_report_byte_private {\n'
            f'inline constexpr uint32_t pc=0x{root:08x}u,word=0x{word:08x}u;\n'
            f'inline constexpr int32_t parent_offset={relative},report_offset={report_offset};\n'
            f'inline constexpr uint8_t expected={value}u;\n'
            f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{next_word:08x}u;\n'
            '}\n')


def expand_report_byte(old, next_entry, report_byte):
    """Expand only the guarded first callee word, preserving all other roots."""
    prior, caller = next_entry
    blocks, info = report_byte
    render_report_byte(report_byte)
    if old != prior or len(caller) != 7:
        raise ValueError('report byte fixture predecessor')
    owner, size, call, call_word, root, entry_word, return_pc = caller
    pc, word, _, _, _, next_pc, next_word, ret = info
    if (not 8 <= size <= 65536 or size % 4 or
            owner & 3 or call & 3 or root & 3 or
            not owner <= call < return_pc < owner + size or
            return_pc != call + 4 or ret != return_pc or
            pc != root or word != entry_word or
            root not in old or owner not in old or
            set(blocks) != set(old) or
            old[root] != (entry_word, GUARD) or
            blocks[root] != (entry_word, next_word, GUARD) or
            not 0 <= (return_pc-owner)//4 < len(old[owner]) or
            old[owner][(return_pc-owner)//4] != GUARD):
        raise ValueError('report byte fixture history')
    if any(blocks[at] != words for at,words in old.items() if at != root):
        raise ValueError('report byte fixture overlap')
    if not 0 <= (call-owner)//4 < len(old[owner]) or old[owner][(call-owner)//4] != call_word:
        raise ValueError('report byte fixture call')
    check_spans({address: 4 * len(words) for address, words in blocks.items()})
    return blocks
