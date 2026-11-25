#!/usr/bin/env python3
"""Private SITransfer packet-free predicate fixture, never publish its address."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_choice_v878 import plan as choice_plan,header as choice_header
from prepare_owner_callback_prefix_v797 import install
from prepare_owner_cancel_v754 import patch_analyzer

def predicate(rows):
    candidates=[]
    for pc,(w,o,k) in rows.items():
        if w>>26!=11 or w&0xffff!=0xffff or w&(1<<21) or o or k:continue
        before=rows.get(pc-4);after=rows.get(pc+4)
        if before is None or after is None or after[0]>>26!=16 or after[0]&3:continue
        ld=before[0]
        if ((ld>>26==32) or (ld>>26==31 and (ld>>1)&1023==23)) and ((ld>>21)&31)==((w>>16)&31):
            candidates.append((pc-4,pc))
    if len(candidates)!=1:raise ValueError('packet predicate shape')
    return candidates[0]

def plan(dol,elf):
    q=choice_plan(dol,elf)
    if tuple(o for _,_,o,_ in q[4])!=(3,4):raise ValueError('packet boundary')
    return q,predicate(q[1])

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q,(probe,compare)=plan(a.dol.read_bytes(),a.elf.read_bytes());base=q[0][0];C=base[1]
        if a.install:install(base,a.output,extra_links=tuple((C,pc,dst) for pc,dst in q[3][1:]),use_reachable=True)
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            choice_header(q,a.output)
            with a.output.open('a') as f:
                f.write(f'inline constexpr uint32_t PacketProbe=0x{probe:08x}u,PacketCompare=0x{compare:08x}u;\n')
            print('V881_PACKET_PREDICATE verified=1 load_compare=1 sentinel=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('packet predicate shape','packet boundary','transfer choice census','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V881_PACKET_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
