#!/usr/bin/env python3
"""Private first original SITransfer direct call, through compiler-save return."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge,names
from audit_handler_deps_v749 import graph
from prepare_owner_callback_prefix_v797 import prefix_geometry,header,install
from prepare_owner_pair_v753 import H,BLR,alias,pair_shape
from prepare_owner_leaf_v714 import bl
from prepare_owner_cancel_v754 import patch_analyzer
from make_private_elf_symbol_map import parse_functions

def plan(dol,elf):
    n,*_=geometry(dol,elf);handler=exact(dol,elf,HANDLER,n)
    _,C,_=edge(HANDLER,handler,7)
    sizes=parse_functions(elf)
    if sizes.get(C)!=91*4 or names(elf,C)!='SITransfer':raise ValueError('transfer extent')
    code=exact(dol,elf,C,91);edges=graph(C,code)
    if len(edges)!=9 or any(k!=1 for k,_ in edges):raise ValueError('transfer edges')
    site,S,prefix=prefix_geometry(C,code)
    if edges[0]!=(1,S):raise ValueError('transfer save')
    save=alias(dol,elf,S,sizes,11);restore=alias(dol,elf,edges[-1][1],sizes,11)
    sb,_,disp=pair_shape(save,restore,11)
    roots={H:[bl(H,C),0x60000000,BLR],C:prefix,S:save}
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=3 or any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('transfer overlap')
    return roots,C,S,site,sb,disp
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:
            header(q,a.output);print('V872_TRANSFER_PREFIX_GEOMETRY verified=1 save_gprs=11 restore_pair=1 original_execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('transfer extent','transfer edges','transfer save','transfer overlap','first call','prefix extent','first direct call','prefix instruction','prefix stack shape','continuation shape','alias root','alias symbol','pair shape','frame offset','save leaf shape','save leaf extent','save leaf sequence','save leaf terminator','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V872_TRANSFER_PREFIX_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
