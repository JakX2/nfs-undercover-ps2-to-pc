#!/usr/bin/env python3
"""Private original callback prologue reached by an emitted synthetic bctrl."""
import argparse
import re
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact
from prepare_owner_pair_v753 import H
from prepare_owner_callback_prefix_v797 import plan as prefix_plan, header as prefix_header, install as prefix_install
from prepare_owner_cancel_v754 import patch_analyzer

def verify_indirect(body, site):
    pat=r'(?mi)^loc_'+f'{site:X}'+r': ;\n.*?(?=^loc_[0-9a-f]+: ;|\Z)'
    m=list(re.finditer(pat,body,re.S|re.M))
    if len(m)!=1:
        raise ValueError('indirect label')
    block=m[0][0]
    if len(re.findall(r'(?mi)^\s*ctx\.lr = 0x'+f'{site+4:X}'+r';[^\n]*$',block))!=1:
        raise ValueError('indirect LR')
    if len(re.findall(r'(?m)^\s*if \(ctx\.ctr\) \{ ctx\.pc = ctx\.ctr; return; \}',block))!=1:
        raise ValueError('indirect dispatch')
    if 'interpret_step' in block or 'micro_interpret' in block:
        raise ValueError('indirect fallback')

def plan(dol,elf):
    roots,C,S,site,sb,disp=prefix_plan(dol,elf)
    roots[H]=[0x4e800421,0x60000000,0x4e800020]
    return (roots,C,S,site,sb,disp),exact(dol,elf,C,172)

def header(p,out):
    q,words=p
    prefix_header(q,out)
    with out.open('a') as f:
        f.write('inline constexpr std::array<uint32_t,172> full_callback_words{'+','.join(f'0x{w:08x}u' for w in words)+'};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:prefix_install(q[0],a.output,indirect_caller=True)
        elif a.patch_analyzer:patch_analyzer(q[0],a.output)
        else:
            header(q,a.output);print('V806_CALLBACK_GEOMETRY verified=1 original_words=172 synthetic_bctrl=1')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('indirect label','indirect LR','indirect dispatch','indirect fallback','native owner','native coverage','hook identity','hook coverage')
        print('V806_CALLBACK_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
