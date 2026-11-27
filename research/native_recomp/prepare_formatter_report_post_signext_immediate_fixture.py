#!/usr/bin/env python3
"""Guarded original 123 zero-input addi after authenticated 122 extsb.

The original 118..122 predecessor is mandatory. Source-only work cannot
install original Wii words: only the private owner may append original 124
behind a synthetic guard. This module never executes original 123.
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

MEM1_BEGIN=0x80000000
MEM1_END=0x81800000
ZERO_INPUT_COUNTS=(0,1,0,0,0,0,0,0,0,0,0)


def decode_li(word):
    if (type(word) is not int or not 0 <= word <= 0xffffffff or
            word >> 26 != 14 or ((word >> 16) & 31) != 0):
        raise ValueError('report next immediate encoding')
    dest=(word >> 21) & 31
    if dest not in (0, *range(3,13)):
        raise ValueError('report next immediate encoding')
    value=word & 0xffff
    return dest, (value|0xffff0000) if value & 0x8000 else value


def promote(signext, immediate, copy, predecessor, compare, following):
    family,name,counts,modeled,reason=inspect_123(
        signext,immediate,copy,predecessor,compare)
    if (family,name,counts,modeled,reason)!=(
            'integer','add_immediate',ZERO_INPUT_COUNTS,1,'supported'):
        raise ValueError('report next immediate provenance')
    if type(following) is not int or not 0 <= following <= 0xffffffff or following == GUARD:
        raise ValueError('report next immediate successor')
    if (not isinstance(signext,tuple) or len(signext)!=2 or
            not isinstance(signext[0],dict) or
            not isinstance(signext[1],tuple) or len(signext[1])!=9):
        raise ValueError('report next immediate predecessor')
    blocks, fields=signext
    root, signext_pc, signext_word, pc, word, prior_dst, prior_before, prior_after, ret=fields
    if (any(type(x) is not int for x in fields) or
            root&3 or not MEM1_BEGIN <= root < MEM1_END-32 or
            signext_pc!=root+16 or pc!=root+20 or
            blocks.get(root) is None or len(blocks[root])!=7 or
            blocks[root][4]!=signext_word or blocks[root][5]!=word or
            blocks[root][-1]!=GUARD or
            ret in tuple(root+4*i for i in range(8))):
        raise ValueError('report next immediate predecessor')
    dst,value=decode_li(word)
    out={**blocks,root:blocks[root][:-1]+(following,GUARD)}
    check_spans({address:4*len(words) for address,words in out.items()})
    return out,(root,pc,word,pc+4,following,dst,value,ret)


def render(contract):
    if (not isinstance(contract,tuple) or len(contract)!=2 or
            not isinstance(contract[1],tuple) or len(contract[1])!=8):
        raise ValueError('report next immediate rendering')
    root,pc,word,next_pc,following,dst,value,ret=contract[1]
    if (any(type(x) is not int for x in contract[1]) or
            root&3 or not MEM1_BEGIN <= root < MEM1_END-32 or
            pc!=root+20 or next_pc!=pc+4 or
            not 0 <= following <= 0xffffffff or following==GUARD or
            (dst,value)!=decode_li(word) or
            ret in tuple(root+4*i for i in range(8))):
        raise ValueError('report next immediate rendering')
    return (
        'namespace formatter_report_post_signext_immediate_private {\n'
        f'inline constexpr uint32_t root=0x{root:08x}u,pc=0x{pc:08x}u,word=0x{word:08x}u;\n'
        f'inline constexpr uint32_t next_pc=0x{next_pc:08x}u,next_word=0x{following:08x}u;\n'
        f'inline constexpr uint32_t return_pc=0x{ret:08x}u;\n'
        f'inline constexpr unsigned destination_reg={dst}u;\n'
        f'inline constexpr uint32_t value=0x{value:08x}u;\n'
        '}\n')


def plan(dol,elf,*,predecessor=None,compare=None,copy=None,
         immediate=None,signext=None):
    if predecessor is None:predecessor=byte_plan(dol,elf,with_live=True)
    if compare is None:compare=compare_plan(dol,elf,predecessor=predecessor)
    if copy is None:copy=copy_plan(dol,elf,predecessor=predecessor,compare=compare)
    if immediate is None:immediate=immediate_plan(
        dol,elf,predecessor=predecessor,compare=compare,copy=copy)
    if signext is None:signext=signext_plan(
        dol,elf,predecessor=predecessor,compare=compare,
        copy=copy,immediate=immediate)
    root=signext[1][0]
    size=parse_functions(elf).get(root,0)
    if not 28 <= size <= 65536 or size%4:
        raise ValueError('report next immediate extent')
    actual=exact_words(dol,elf,root,7)
    if (len(actual)!=7 or tuple(actual[:6])!=tuple(signext[0][root][:6])):
        raise ValueError('report next immediate original')
    return promote(signext,immediate,copy,predecessor,compare,actual[6])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dol',type=Path)
    parser.add_argument('elf',type=Path)
    q=parser.parse_args()
    safe={
        'size','report next immediate provenance','report next immediate successor',
        'report next immediate predecessor','report next immediate encoding',
        'report next immediate rendering','report next immediate extent',
        'report next immediate original',
    }
    try:
        if (not 256 <= q.dol.stat().st_size <= MAX_DOL or
                not 52 <= q.elf.stat().st_size <= 64*1024*1024):
            raise ValueError('size')
        with plan_cache_scope():
            contract=plan(q.dol.read_bytes(),q.elf.read_bytes())
        render(contract)
    except (OSError,ValueError,TypeError,KeyError,IndexError,
            struct.error) as error:
        reason=str(error)
        print('FORMATTER_123_IMMEDIATE_FIXTURE verified=0 reason='+
              (reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print('FORMATTER_123_IMMEDIATE_FIXTURE verified=1 previous_122_fixture=1 '
          'instruction_123=zero_input_addi native_execution=0 '
          'next_guard=1 original_execution=0')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
