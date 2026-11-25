#!/usr/bin/env python3
"""Private SITransfer packet-free predicate fixture, never publish its address."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_choice_v878 import plan as choice_plan,header as choice_header
from prepare_owner_callback_prefix_v797 import install
from prepare_owner_cancel_v754 import patch_analyzer
from make_private_elf_symbol_map import HEADER,SECTION,parse_functions
from prepare_v419_full_start import u32

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

def first_predicate(rows):
    loads,branches,compares=predicate(rows)
    probe=min(rows);w,o,k=rows[probe]
    cmp=rows.get(probe+8,(0,0,0))[0]
    branch=rows.get(probe+12,(0,0,0))[0]
    if probe not in loads or o or k or w>>26!=32 or cmp>>26!=11 or cmp&0xffff!=0xffff or cmp&(1<<21) or ((w>>21)&31)!=((cmp>>16)&31) or branch>>26!=16 or branch&3:
        raise ValueError('packet first predicate')
    # The intervening instruction must not overwrite the observed load
    # register; the native fixture checks that value again at the compare.
    return probe,probe+8

def writable_spans(dol,elf):
    parse_functions(elf)
    head=HEADER.unpack_from(elf);shoff,shnum=head[6],head[12]
    sections=[]
    for i in range(shnum):
        _,kind,flags,base,off,size,*_=SECTION.unpack_from(elf,shoff+i*SECTION.size)
        if kind not in (1,8) or flags&7!=3 or not size:continue
        if kind==1 and off+size>len(elf):raise ValueError('packet data extent')
        if not 0x80000000<=base<base+size<=0x81800000:continue
        sections.append((base,base+size))
    # Intersect with the independently authenticated DOL's data/BSS ranges.
    data=[]
    for i in range(7,18):
        off,base,size=(u32(dol,b+4*i) for b in (0,0x48,0x90))
        if not size:continue
        if off<256 or off+size>len(dol) or base+size>2**32:raise ValueError('packet data extent')
        data.append((base,base+size))
    base,size=u32(dol,0xd8),u32(dol,0xdc)
    if size and base+size<=2**32:data.append((base,base+size))
    result=sorted(set((max(a,c),min(b,d)) for a,b in sections for c,d in data if max(a,c)<min(b,d)))
    if not 1<=len(result)<=64:raise ValueError('packet data extent')
    return result

def plan(dol,elf):
    q=choice_plan(dol,elf)
    if tuple(o for _,_,o,_ in q[4])!=(3,4):raise ValueError('packet boundary')
    return q,(predicate(q[1]),first_predicate(q[1]),writable_spans(dol,elf))

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q,((loads,branches,compares),(probe,compare),spans)=plan(a.dol.read_bytes(),a.elf.read_bytes());base=q[0][0];C=base[1]
        if a.install:install(base,a.output,extra_links=tuple((C,pc,dst) for pc,dst in q[3][1:]),use_reachable=True)
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            choice_header(q,a.output)
            with a.output.open('a') as f:
                f.write(f'inline constexpr std::array<uint32_t,{len(loads)}> PacketProbes{{'+','.join(f'0x{pc:08x}u' for pc in loads)+'};\n')
                f.write(f'inline constexpr uint32_t PacketProbe=0x{probe:08x}u,PacketCompare=0x{compare:08x}u;\n')
                f.write('struct PacketSpan{uint32_t lo,hi;};\n')
                f.write(f'inline constexpr std::array<PacketSpan,{len(spans)}> PacketDataSpans{{{{'+','.join(f'{{0x{lo:08x}u,0x{hi:08x}u}}' for lo,hi in spans)+'}};\n')
            print(f'V885_PACKET_DATA verified=1 sections={len(spans)} first_predicate=1 execution=0')
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
        safe=('packet predicate shape','packet first predicate','packet data extent','packet boundary','transfer choice census','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V881_PACKET_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
