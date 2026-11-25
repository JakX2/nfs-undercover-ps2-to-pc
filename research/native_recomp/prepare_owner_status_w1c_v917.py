#!/usr/bin/env python3
"""Private original resumed SI handler prefix, through exact status load."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v868_handler_suffix import lane
from audit_handler_path_v887 import unique_prefix,step
from audit_handler_frontier_v896 import paths
from audit_handler_index_v902 import classify_index
from prepare_owner_packet_choice_v881 import writable_spans
from prepare_owner_restore_v735 import H,BLR,caller,header
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root
from prepare_owner_scheduler_v722 import reachable
from audit_handler_suffix_v728 import target
from prepare_owner_cancel_v754 import patch_analyzer
from audit_handler_branch_frontier_v907 import frontier
from audit_handler_path_v887 import classify

def plan(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf);start=sites[0]+4
    rows=lane(HANDLER,words,start,(52,0,1,((1,7),(1,8),(1,12))))
    if unique_prefix(rows,start)[0]!='si_status':raise ValueError('status identity')
    code=[rows[start+4*i][0] for i in range(12)]
    if [w>>26 for w in code[:10]] != [15,15,21,15,31,32,21,14,31,36] or (code[4]>>1)&1023!=792:raise ValueError('status prefix shape')
    if paths(rows,start,10)!=[('store','si_status',36)] or any(rows[start+4*i][1:]!=(0,0) for i in range(12)):raise ValueError('status store identity')
    if code[-1]>>26!=31 or (code[-1]>>1)&1023!=23:raise ValueError('indexed load identity')
    cmp,branch=[rows[start+4*i][0] for i in (12,13)]
    bo,bi=(branch>>21)&31,(branch>>16)&31
    if cmp>>26!=10 or cmp&(1<<21) or ((cmp>>16)&31)!=((code[-1]>>21)&31) or branch>>26!=16 or branch&3 or not bo&4 or bo&16 or bi//4!=(cmp>>23)&7 or bi%4==3:raise ValueError('channel compare shape')
    dest=target(start+52,branch)
    if not start+56<dest<=start+4*63 or dest not in rows or start+56 not in rows:raise ValueError('channel branch extent')
    code += [cmp,branch]
    selected={pc:BLR if kind else w for pc,(w,ordinal,kind) in rows.items()}
    if len(selected)!=52 or any(selected.get(start+4*i)!=w for i,w in enumerate(code)):raise ValueError('full suffix identity')
    boundaries=[(pc,w,ordinal) for pc,(w,ordinal,kind) in sorted(rows.items()) if kind]
    if {o for _,_,o in boundaries}!={7,8,12} or any(w>>26!=18 or w&3!=1 for _,w,_ in boundaries):raise ValueError('full suffix boundaries')
    code=[selected.get(a,0x60000000) for a in range(start,max(selected)+4,4)]
    if set(reachable(start,code))!=set(selected):raise ValueError('channel branch reachability')
    return start,code,0,0

def boundaries(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf);start=sites[0]+4
    rows=lane(HANDLER,words,start,(52,0,1,((1,7),(1,8),(1,12))))
    return [(pc,word,ordinal) for pc,(word,ordinal,kind) in sorted(rows.items()) if kind]

def branch_seeds(code):
    cmp,branch=code[12:14];imm=cmp&0xffff;bo,bi=(branch>>21)&31,(branch>>16)&31
    chosen={}
    for v in sorted({0,1,imm,max(0,imm-1),imm+1,0xffffffff}):
        condition=(v<imm,v>imm,v==imm)[bi%4]
        chosen.setdefault(int(condition==bool(bo&8)),v)
    if set(chosen)!={0,1}:raise ValueError('channel branch seeds')
    return chosen[0],chosen[1]

def status_mask(code,seed,status):
    # Independent public PPC integer semantics, actual private words.
    r=tuple(seed)
    for i,w in enumerate(code[:9]):
        op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        if i==5:
            if op!=32:raise ValueError('load identity')
            out=list(r);out[rs]=status;r=tuple(out)
        elif op==31 and xo in (60,536):
            out=list(r)
            x,y=r[rs],r[rb]
            out[ra]=None if x is None or y is None else (x&~y)&0xffffffff if xo==60 else 0 if y&32 else x>>(y&31)
            r=tuple(out)
        else:r=step(w,r)
    return r[(code[9]>>21)&31]

def channel_register(code):
    # Authenticate one nonvolatile input as the channel selector; do not
    # expose the original register number in public logs. Check varied
    # status patterns AND unrelated register values.
    hits=[]
    statuses=(0,0x0f0f0f0f,0x08080808,0x01020408,0xffffffff)
    for reg in range(14,32):
        good=True
        for seed in (0,0x13579bdf):
            for ch in range(4):
                regs=[seed^((i*0x1234567)&0xffffffff) if seed else 0 for i in range(32)]
                regs[reg]=ch
                for status in statuses:
                    expected=status&(0x0f<<((3-ch)*8))
                    if status_mask(code,regs,status)!=expected:good=False;break
                if not good:break
            if not good:break
        if good:hits.append(reg)
    if len(hits)!=1:raise ValueError('channel selector identity')
    return hits[0]

def install(p,root):
    L,code,_,_=p;paths=sorted(root.glob('*.cpp'))
    if not paths or any(p.is_symlink() for p in paths):raise ValueError('private output')
    src={p:p.read_text() for p in paths}
    main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    outer=src[main].split('extern "C" void run_game(',1)[1]
    expected={a+4*i:(a,w) for a,ws in ((H,caller(L)),(L,code)) for i,w in enumerate(ws) if a+4*i in reachable(a,ws)}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    owners=[exact_function(s,H) for s in src.values() if owns_root(s,H)]
    if len(owners)!=1:raise ValueError('caller owner')
    verify_direct(owners[0],H,L)
    hooks={pc:w for pc,(_,w) in expected.items()};seen=set();changes={}
    for p,s in src.items():
        old=s
        for pc,w in hooks.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            m=list(pat.finditer(s))
            if not m:continue
            if len(m)!=1 or pc in seen:raise ValueError('hook identity')
            seen.add(pc);s=pat.sub(lambda m:m[0]+f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',s,count=1)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            if s.count(a)!=1:raise ValueError('include')
            changes[p]=s.replace(a,a+'\n#include "rfi_test_v708.h"')
    if seen!=set(hooks):raise ValueError('hook coverage')
    for p,s in changes.items():p.write_text(s)
    print(f'V917_NATIVE_ROUTE labels={len(expected)} original_branch=1 stops=2 fallback=0 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());root,code,_,_=q
        channel=channel_register(code)
        candidates=classify_index(code[:12]);seeds=branch_seeds(code)
        if len(candidates)!=1 or candidates[0][0] is not None or candidates[0][2]!=4:raise ValueError('indexed table provenance')
        addresses=candidates[0][1];spans=writable_spans(a.dol.read_bytes(),a.elf.read_bytes())
        if any(a&3 or sum(lo<=a and a+4<=hi for lo,hi in spans)!=1 for a in addresses):raise ValueError('indexed table extent')
        from audit_handler_arm_v913 import arm_address
        # Private geometry independently identifies a single inherited
        # nonvolatile pointer. The address is a synthetic fixture allocation,
        # not a claim that original startup initializes this register here.
        candidates2=[]
        for reg in range(14,32):
            if reg==channel:continue
            x=arm_address(code,0,seeds[0],0x13579bdf,(reg,0x80090000))[2]
            y=arm_address(code,0,seeds[0],0x13579bdf,(reg,0x800a0000))[2]
            if x is not None and y is not None and (y-x)&0xffffffff==0x10000:candidates2.append(reg)
        if len(candidates2)!=1:raise ValueError('arm input identity')
        arm_reg=candidates2[0];arm_base=0x80090000
        arm_results=[arm_address(code,ch,seeds[0],seed,(arm_reg,arm_base)) for seed in (0,0x13579bdf) for ch in range(4)]
        if arm_results[:4]!=arm_results[4:] or any(i!=16 or w>>26!=31 or (w>>1)&1023!=23 or a is None or a&3 or not 0x80080000<=a<=0x800afffc for i,w,a in arm_results):raise ValueError('arm input extent')
        arm_addresses=[a for _,_,a in arm_results[:4]]
        if len(set(arm_addresses))!=4 or any(a in addresses or H<=a<H+4*len(caller(root)) or root<=a<root+4*len(code) for a in arm_addresses):raise ValueError('arm input overlap')
        if a.install:install(q,a.output)
        elif a.patch_analyzer:patch_analyzer(({H:caller(root),root:code},),a.output)
        else:
            header(q,a.output)
            with a.output.open('a') as f:
                f.write(f'inline constexpr unsigned StatusChannelRegister={channel}u;\n')
                f.write('inline constexpr std::array<uint32_t,4> ChannelTable{'+','.join(f'0x{a:08x}u' for a in addresses)+'};\n')
                f.write('inline constexpr std::array<uint32_t,2> BranchSeeds{'+','.join(f'0x{a:08x}u' for a in seeds)+'};\n')
                pcs=sorted(reachable(root,code))
                f.write(f'inline constexpr std::array<uint32_t,{len(pcs)}> ArmLabels{{'+','.join(f'0x{a:08x}u' for a in pcs)+'};\n')
                f.write(f'inline constexpr uint32_t BranchDestination=0x{target(root+52,code[13]):08x}u;\n')
                f.write(f'inline constexpr unsigned ArmInputRegister={arm_reg}u;\ninline constexpr uint32_t ArmInputBase=0x{arm_base:08x}u;\n')
                f.write('inline constexpr std::array<uint32_t,4> ArmInputAddresses{'+','.join(f'0x{a:08x}u' for a in arm_addresses)+'};\n')
                ends=boundaries(a.dol.read_bytes(),a.elf.read_bytes())
                f.write('struct SuffixBoundary{uint32_t pc,word;unsigned ordinal;};\n')
                f.write(f'inline constexpr std::array<SuffixBoundary,{len(ends)}> SuffixBoundaries{{{{'+','.join(f'{{0x{pc:08x}u,0x{word:08x}u,{ordinal}u}}' for pc,word,ordinal in ends)+'}};\n')
            print('V917_STATUS_GEOMETRY verified=1 prefix=5 original_load=1 original_store=1 synthetic_stop=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('full suffix identity','full suffix boundaries','arm input identity','arm input extent','arm input overlap','arm shape','arm overlap','arm word','channel compare shape','channel branch extent','channel branch reachability','channel branch seeds','indexed table provenance','indexed table extent','indexed load identity','channel selector identity','load identity','status store identity','status identity','status prefix shape','native coverage','caller owner','hook identity','include','hook coverage','private output')
        print('V917_STATUS_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
