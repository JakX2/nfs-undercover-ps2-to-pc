#!/usr/bin/env python3
"""Authentic EXIImm/EXISync write routines in a synthetic SRAM transaction."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE
from make_private_elf_symbol_map import parse_functions
from prepare_owner_wireless_lock_v819 import plan as lock_plan
from prepare_owner_wireless_v816 import install as old_install
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_pair_v753 import alias,pair_shape
from prepare_owner_leaf_v714 import H,bl
from audit_callback_frontiers_v799 import call_sites
from make_start_to_exi_transaction_v56 import IMM,SYNC,HWREV,UNMASK,GETIRQ
from make_start_to_eximask_v53 import MASK
from audit_handler_third_v740 import names
from audit_callback_posttime_v812 import SDK
BLR=0x4e800020
SETMASK=0x805266e0

def caller():
    words=[]
    for i in range(12):
        # r14 is the explicit synthetic command/payload buffer base.
        # Reinitialize caller-volatile ABI args for each original call.
        words.extend([0x38600000,0x388e0000|(4*i),0x38a00004,0x38c00001,0x38e00000])
        words.append(bl(H+4*len(words),IMM))
        words.append(0x38600000)
        words.append(bl(H+4*len(words),SYNC))
    return words+[0x60000000,BLR]

def plan(dol,elf):
    q,*_=lock_plan(dol,elf);old=q[0];sizes=parse_functions(elf)
    if sizes.get(IMM)!=636 or sizes.get(SYNC)!=636 or sizes.get(HWREV)!=16:
        raise ValueError('transfer extent')
    iw,sw,hw=exact(dol,elf,IMM,159),exact(dol,elf,SYNC,159),exact(dol,elf,HWREV,4)
    isites,ssites=call_sites(IMM,iw),call_sites(SYNC,sw)
    if len(isites)!=6 or len(ssites)!=4 or any(k!=1 for _,k,_ in isites+ssites):
        raise ValueError('transfer calls')
    deps=[a for _,_,a in isites[1:-1]]
    if deps[:2]!=[DISABLE,RESTORE] or deps[2] not in (MASK,UNMASK) or deps[3]!=RESTORE:
        raise ValueError('immediate dependencies')
    children=[a for _,_,a in ssites]
    if children[0]!=DISABLE or children[1]!=HWREV or children[3]!=RESTORE or sizes.get(children[2])!=644:
        raise ValueError('sync dependencies')
    guard=children[2];exact(dol,elf,guard,1)
    S,F=isites[0][2],isites[-1][2]
    n=32-((exact(dol,elf,S,1)[0]>>21)&31)
    if not 1<=n<=18:raise ValueError('alias count')
    save=alias(dol,elf,S,sizes,n);restore=alias(dol,elf,F,sizes,n)
    _,base,disp=pair_shape(save,restore,n)
    roots={H:caller(),IMM:iw,SYNC:sw,HWREV:hw,S:save,F:restore,guard:[BLR]}
    for a in (DISABLE,RESTORE,MASK,UNMASK,SETMASK,GETIRQ):
        if a in roots:raise ValueError('root overlap')
        roots[a]=old[a]
    if call_sites(HWREV,hw):raise ValueError('revision leaf')
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>x for (_,y),(x,_) in zip(spans,spans[1:])):raise ValueError('root overlap')
    return roots,S,F,n,base,disp,guard

def header(p,out):
    roots,S,F,n,base,disp,g=p
    fmt=lambda xs:','.join(f'0x{v:08x}u' for v in xs)
    with out.open('x') as f:
        f.write('#pragma once\n#include <array>\n#include <cstdint>\n#include <span>\n')
        vals={'H':H,'Imm':IMM,'Sync':SYNC,'Revision':HWREV,'D':DISABLE,'R':RESTORE,'SaveAlias':S,'RestoreAlias':F,'ConsoleGuard':g,'Stop':H+4*(len(roots[H])-2)}
        f.write('inline constexpr uint32_t '+','.join(f'{k}=0x{v:08x}u' for k,v in vals.items())+';\n')
        f.write(f'inline constexpr unsigned AliasCount={n},RestoreBase={base};\ninline constexpr int32_t AliasDisp={disp};\n')
        for i,(a,ws) in enumerate(roots.items()):
            f.write(f'inline constexpr std::array<uint32_t,{len(ws)}> words_{i}{{'+fmt(ws)+'};\n')
        f.write('struct Root{uint32_t address;std::span<const uint32_t> words;};\n')
        f.write(f'inline constexpr std::array<Root,{len(roots)}> roots{{{{'+','.join(
            f'Root{{0x{a:08x}u,words_{i}}}' for i,a in enumerate(roots))+'}};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());roots,S,F,n,base,disp,g=q
        if a.install:
            old_install((roots,0,0,0,0,(g,)),a.output)
            print('V828_EXI_NATIVE_ROUTE verified=1 original_imm=1 original_sync=1 console_guard=1 execution=0')
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:
            header(q,a.output);print(f'V828_EXI_GEOMETRY verified=1 imm_words=159 sync_words=159 aliases={n} transfers=12')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('transfer extent','transfer calls','immediate dependencies','sync dependencies','alias count','root overlap','revision leaf','native coverage','native owner','native edge','hook identity','hook include','hook coverage')
        print('V828_EXI_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
