#!/usr/bin/env python3
"""Authenticate both original selected callee prologues and GPR-save aliases."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_callee_v895 import plan as selected_plan
from prepare_owner_callback_prefix_v797 import prefix_geometry,header,install
from prepare_owner_pair_v753 import H,BLR,alias
from prepare_owner_leaf_v714 import bl
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_v667_si_dispatch import exact
from classify_save_leaf_v683 import classify_suffix
from make_private_elf_symbol_map import parse_functions

def plan(dol,elf,lane):
    q=selected_plan(dol,elf);_,C,old,control=q[-1][lane-5]
    sizes=parse_functions(elf);n=sizes.get(C,0)
    if not 4<n<=4096 or n%4:raise ValueError('callee extent')
    code=exact(dol,elf,C,n//4)
    site,S,prefix=prefix_geometry(C,code)
    if prefix[:len(old)-1]!=old[:-1] or site!=C+4*(len(old)-1) or prefix[len(old)-1]!=control:raise ValueError('callee prefix identity')
    save=alias(dol,elf,S,sizes,lane)
    info=classify_suffix(save)
    if info['kind']!=1 or info['registers']!=lane:raise ValueError('callee save identity')
    disp=((save[0]&0xffff)^0x8000)-0x8000
    roots={H:[bl(H,C),0x60000000,BLR],C:prefix,S:save}
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if len(roots)!=3 or any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('callee fixture overlap')
    return roots,C,S,site,info['base'],disp

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path);p.add_argument('--lane',type=int,choices=(5,6),required=True)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes(),a.lane)
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(q,a.output)
        else:
            header(q,a.output);print(f'V899_CALLEE_SAVE_GEOMETRY lane={a.lane} verified=1 save_gprs={a.lane} original_execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('callee extent','callee prefix identity','callee save identity','callee fixture overlap','first call','prefix extent','first direct call','prefix instruction','prefix stack shape','continuation shape','alias root','alias symbol','save leaf shape','save leaf extent','save leaf sequence','save leaf terminator','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V899_CALLEE_SAVE_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
