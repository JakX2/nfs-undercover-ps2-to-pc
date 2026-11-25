#!/usr/bin/env python3
"""Private SITransfer packet-free predicate fixture, never publish its address."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_choice_v878 import plan as choice_plan,header as choice_header
from prepare_owner_callback_prefix_v797 import install
from prepare_owner_cancel_v754 import patch_analyzer

def predicate(rows):
    # Recognize the bounded original memory reads, not an assumed compiler
    # adjacency pattern. Actual dependency is demonstrated by fresh-state
    # replay and identical per-channel effective addresses.
    loads=[];branches=compares=0
    for pc,(w,o,k) in sorted(rows.items()):
        op=w>>26;xo=(w>>1)&1023
        if o or k:continue
        if op==32 or (op==31 and xo==23):loads.append(pc)
        if op==16:branches+=1
        if op in (10,11) or op==31 and xo in (0,32):compares+=1
    if not 1<=len(loads)<=4 or not 1<=branches<=4 or not 1<=compares<=4:
        raise ValueError('packet predicate shape')
    return loads,branches,compares

def plan(dol,elf):
    q=choice_plan(dol,elf)
    if tuple(o for _,_,o,_ in q[4])!=(3,4):raise ValueError('packet boundary')
    return q,predicate(q[1])

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q,(loads,branches,compares)=plan(a.dol.read_bytes(),a.elf.read_bytes());base=q[0][0];C=base[1]
        if a.install:install(base,a.output,extra_links=tuple((C,pc,dst) for pc,dst in q[3][1:]),use_reachable=True)
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            choice_header(q,a.output)
            with a.output.open('a') as f:
                f.write(f'inline constexpr std::array<uint32_t,{len(loads)}> PacketProbes{{'+','.join(f'0x{pc:08x}u' for pc in loads)+'};\n')
            print(f'V882_PACKET_PREDICATE verified=1 loads={len(loads)} branches={branches} compares={compares} execution=0')
            for i,(pc,(w,o,k)) in enumerate(sorted(q[1].items()),1):
                op=w>>26;xo=(w>>1)&1023
                if op in (10,11):
                    imm=w&0xffff;cls=0 if imm==0 else 1 if imm==0xffff else 2 if imm<=3 else 3
                    print(f'V883_PACKET_COMPARE index={i} mode=immediate value_class={cls}')
                elif op==31 and xo in (0,32):print(f'V883_PACKET_COMPARE index={i} mode=register value_class=4')
                elif op==16:print(f'V883_PACKET_CONTROL index={i} kind={(w>>16)&3}')
                elif pc in loads:print(f'V883_PACKET_READ index={i} indexed={int(op==31)}')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('packet predicate shape','packet boundary','transfer choice census','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V881_PACKET_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
