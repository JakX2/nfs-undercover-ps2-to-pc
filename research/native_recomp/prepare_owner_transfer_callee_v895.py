#!/usr/bin/env python3
"""Private SITransfer available-packet original time return."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_packet_choice_v881 import plan as packet_plan
from prepare_owner_transfer_choice_v878 import header as choice_header,choice
from prepare_owner_callback_prefix_v797 import install
from prepare_owner_cancel_v754 import patch_analyzer
from si_nested_geometry_v693 import nested_plan
from audit_os_leaf_v703 import plan as leaf_plan
from audit_handler_third_v740 import summarize
from prepare_owner_pair_v753 import BLR
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions

def callee_prefix(dol,elf,root,sizes):
    size=sizes.get(root,0)
    if not 4<size<=4096 or size%4:raise ValueError('callee extent')
    code=list(exact(dol,elf,root,size//4))
    for i,w in enumerate(code[:32]):
        op,xo=w>>26,(w>>1)&1023
        if op in (16,17,18,19) or (op==31 and xo==146):
            if not i:raise ValueError('callee empty prefix')
            return code[:i]+[BLR],w
    raise ValueError('callee prefix bound')

def plan(dol,elf):
    q,meta=packet_plan(dol,elf);base=q[0][0];roots,C,S,*_=base
    ts,T=q[3][3]
    _,root,_,_,tw=nested_plan(dol,elf)
    summary,_=summarize(T,tw)
    if T!=root or len(tw)!=25 or summary['direct']!=3 or any(summary[k] for k in ('conditional','backward','indirect','tail','mtmsr','system')) or tw[-1]!=BLR:raise ValueError('transfer time shape')
    leaves=leaf_plan(dol,elf);D,U,R=[x[1] for x in leaves]
    if D!=q[0][1] or list(roots[D])!=list(leaves[0][5]) or T not in q[2] or R not in q[2] or U in roots:raise ValueError('transfer time roots')
    roots[T]=list(tw);roots[U]=list(leaves[1][5]);roots[R]=list(leaves[2][5])
    q=(q[0],q[1],[a for a in q[2] if a not in (T,R)],q[3],q[4])
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('transfer time overlap')
    rows,stops=choice(C,roots[C],ts+4)
    if not stops or any(k!=1 or o not in (5,6,7,8,9) for _,k,o,_ in stops):raise ValueError('post time boundary')
    if tuple(o for _,_,o,_ in stops)!=(5,6):raise ValueError('callee boundary set')
    sizes=parse_functions(elf)
    callees=[]
    for ordinal in (5,6):
        site,addr=q[3][ordinal-1]
        if addr not in q[2] or roots[addr]!=[BLR]:raise ValueError('callee guard identity')
        words,stop=callee_prefix(dol,elf,addr,sizes)
        roots[addr]=words
        callees.append((site,addr,words,stop))
    q=(q[0],q[1],[a for a in q[2] if a not in [x[1] for x in callees]],q[3],q[4])
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('callee overlap')
    return q,meta,T,U,R,ts,leaves,rows,stops,callees

def header(p,out):
    q,meta,T,U,R,ts,leaves,rows,stops,callees=p;roots,C,*_=q[0][0]
    (_,_,_),(probe,compare),spans=meta
    choice_header(q,out)
    f=lambda w:f'0x{w:08x}u'
    with out.open('a') as h:
        h.write(f'inline constexpr uint32_t PacketProbe={f(probe)},PacketCompare={f(compare)};\n')
        h.write('struct PacketSpan{uint32_t lo,hi;};\n')
        h.write(f'inline constexpr std::array<PacketSpan,{len(spans)}> PacketDataSpans{{{{'+','.join(f'{{{f(lo)},{f(hi)}}}' for lo,hi in spans)+'}};\n')
        h.write('inline constexpr uint32_t '+','.join(f'{k}={f(v)}' for k,v in (('T',T),('U',U),('R',R),('TimeCall',ts),('TimeResume',ts+4)))+';\n')
        for name,words in (('system_words',roots[T]),('time_words',roots[U]),('irq_restore_words',roots[R])):
            h.write(f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(map(f,words))+'};\n')
        h.write('inline constexpr std::array<uint32_t,2> time_continuation{'+','.join(map(f,roots[C][(ts-C)//4:(ts-C)//4+2]))+'};\n')
        h.write('#include "wii_callback_time_v810.h"\n')
        h.write('inline constexpr undercover::wii::CallbackTimeExpectation transfer_time_expected{'+','.join(map(f,(C,C+364,ts,ts,T)))+
                ',time_continuation,system_words,{{'+','.join('undercover::wii::PostAckLeafExpectation{'+','.join(map(f,l[:4]))+f',{l[4]}u'+'}' for l in leaves)+'}},0x800030d8u};\n')
        h.write(f'inline constexpr std::array<undercover::wii::HandlerSuffixLabel,{len(rows)}> post_time_rows{{{{'+','.join(f'{{{f(pc)},{f(w)},{o}u,{k}u}}' for pc,(w,o,k) in sorted(rows.items()))+'}};\n')
        for name,(site,addr,words,stop) in zip(('Alarm','Immediate'),callees):
            h.write(f'inline constexpr uint32_t {name}Site={f(site)},{name}Root={f(addr)},{name}Stop={f(addr+4*(len(words)-1))},{name}OriginalControl={f(stop)};\n')
            h.write(f'inline constexpr std::array<uint32_t,{len(words)}> {name}Words{{'+','.join(map(f,words))+'};\n')
    print('V895_CALLEE_PREFIX_CENSUS roots=2 alarm_words='+str(len(callees[0][2])-1)+' immediate_words='+str(len(callees[1][2])-1)+' synthetic_stop=1 execution=0')
    print(f'V895_POST_TIME_CENSUS labels={len(rows)} boundaries={len(stops)} ordinals='+','.join(str(o) for _,_,o,_ in stops)+' execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());base=q[0][0][0];C=base[1]
        if a.install:install(base,a.output,extra_links=tuple((C,pc,dst) for pc,dst in q[0][3][1:])+tuple((q[2],l[0],l[1]) for l in q[6]),use_reachable=True)
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            header(q,a.output);print('V895_TRANSFER_TIME_GEOMETRY verified=1 original_time_words=25 leaves=3 packet_predicate=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('callee extent','callee empty prefix','callee prefix bound','callee boundary set','callee guard identity','callee overlap','post time boundary','transfer choice census','transfer time shape','transfer time roots','transfer time overlap','packet predicate shape','packet first predicate','packet data extent','packet boundary','native coverage','native owner','hook identity','hook coverage','private output')
        print('V895_TRANSFER_TIME_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
