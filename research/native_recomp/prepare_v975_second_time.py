#!/usr/bin/env python3
"""Extend the authenticated live second ACK route through its original time helper."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import HANDLER,DISABLE,TIME,RESTORE,exact
from audit_handler_third_v740 import edge as handler_edge
from prepare_v789_alarm_suffix import expectations as callback_expectations
from prepare_owner_second_time_v966 import plan as time_plan
from prepare_owner_second_shared_v988 import admit_shared_time
from prepare_owner_second_ack_v955 import plan as ack_plan
from prepare_owner_second_dispatch_v946 import reachable
from prepare_v958_second_ack import patch_label,render
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v807_callback_prefix import SI
from prepare_v850_callback_return import BLOCK_END

def shared_label(body,pc,w,root,guard):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('time shared label')
    start=hits[0].end();stop=BLOCK_END.search(body,start);end=stop.start() if stop else len(body)
    block=body[start:end]
    if block.count(SI)!=1 or block.count('++ctx.inst_count;')!=1 or 'v958::' in block:raise ValueError('time shared tick')
    if block.index('++ctx.inst_count;')>block.index(SI):raise ValueError('time shared tick')
    old=f'    undercover::wii::v922::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    if root==TIME:
        # The old timebase leaf observer is gated by second-dispatch state.
        # Keep that behavior for the original dispatcher, but disable it
        # once the second handler takes ownership.
        a='if(!undercover::wii::v922::second_dispatch_active_now()) '
        block=replace_exact(block,a,'if(!undercover::wii::v958::active()&&!undercover::wii::v922::second_dispatch_active_now()) ')
        old=f'    undercover::wii::v922::second_dispatch_before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(guard).lower()});\n'
    elif guard:raise ValueError('time shared guard')
    block=replace_exact(block,old,'    if(!undercover::wii::v958::active()) '+old.lstrip())
    i=block.index(SI)+len(SI)
    block=block[:i]+f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(guard).lower()});\n'+block[i:]
    return body[:start]+block+body[end:]

def patch_existing(body,pc,w,old_guard,new_guard):
    a=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(old_guard).lower()});\n'
    b=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(new_guard).lower()});\n'
    return replace_exact(body,a,b) if a!=b else body if body.count(a)==1 else fail('time old hook')

def fail(msg):raise ValueError(msg)

def render_time(old,roots,extra,site,msr):
    # Base configuration is kept for ACK-only and post-ACK runs.
    a='#pragma once\n'
    s=replace_exact(old,a,a+'#define UNDERCOVER_V975_PRIVATE_TIME 1\n')
    order=[HANDLER,*[dst for _,dst,_,_,_ in extra[:3]],DISABLE,TIME,RESTORE]
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    return s+'namespace undercover::wii::v958 {\n'+f'inline constexpr uint32_t time_call=0x{site:08x}u;\n' + \
        'inline constexpr std::array<AckCallSpan,7> time_spans{{'+','.join('{'+fmt((r,r+4*len(roots[r])))+'}' for r in order)+'}};\n'+ \
        'inline constexpr std::array<AckCallEdge,7> time_edges{{'+','.join('{'+fmt((p,t))+'}' for p,t,_,_,_ in extra)+'}};\n'+ \
        'inline constexpr std::array<AckMsrSite,2> msr_sites{{'+','.join('{'+fmt(m)+'}' for m in msr)+'}};\n}\n'

def render_shared(old,extra,site):
    if len(extra)!=8 or extra[-1][0]!=site:raise ValueError('shared time geometry')
    s=replace_exact(old,'#define UNDERCOVER_V975_PRIVATE_TIME 1\n','#define UNDERCOVER_V975_PRIVATE_TIME 1\n#define UNDERCOVER_V989_PRIVATE_SHARED 1\n')
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    return s+'namespace undercover::wii::v958 {\n'+f'inline constexpr uint32_t completion_time_call=0x{site:08x}u;\n'+ \
        'inline constexpr std::array<AckCallEdge,8> shared_edges{{'+','.join('{'+fmt((a,b))+'}' for a,b,_,_,_ in extra)+'}};\n}\n'

def install(dol,elf,root,frontier=False,shared=False,success_frontier=False):
    if success_frontier and not (frontier and shared):raise ValueError('success frontier mode')
    previous=ack_plan(dol,elf);old_roots,_,indirect,_,_,_,old_guard,old_extra=previous
    q,site,msr,_=time_plan(dol,elf);roots,_,_,_,_,_,guard,extra=q
    base_extra=extra
    shared_edge=admit_shared_time(dol,elf,roots,guard,extra) if shared else None
    if shared_edge:extra=(*extra,shared_edge)
    order=[HANDLER,*[dst for _,dst,_,_,_ in extra[:3]],DISABLE,TIME,RESTORE]
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('time tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={};count=0
    for a,legacy in zip(order,('v672','v680','v688','v693','','','')):
        owners=[p for p,s in src.items() if owns_root(s,a)]
        if len(owners)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('time owner')
        p=owners[0];s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        original=exact(dol,elf,a,len(roots[a]))
        expected={pc:(a,original[(pc-a)//4]) for pc in reachable(a,roots[a],guard,indirect)}
        audit_native([body] if legacy=='v680' else src.values(),outer,expected)
        for call_site,dst,_,_,_ in extra:
            if a<=call_site<a+4*len(original):verify_direct(body,call_site,dst)
        old_pcs=reachable(a,old_roots[a],old_guard,indirect) if legacy else set()
        for pc,(_,w) in expected.items():
            if not legacy:out=shared_label(out,pc,w,a,pc in guard)
            elif pc in old_pcs:out=patch_existing(out,pc,w,pc in old_guard,pc in guard)
            else:out=patch_label(out,pc,w,legacy,pc in guard)
        if out!=body:s=replace_exact(s,body,out)
        inc='#include "undercover/wii_second_ack_live_v958.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s;count+=len(expected)
    private=root/'nWiiRuntime/include/undercover/v958_private_second_ack.h'
    if private.is_symlink() or private.parent.is_symlink() or not private.is_file():raise ValueError('time destination')
    previous_header=private.read_text()
    if previous_header!=render(old_roots,old_extra):raise ValueError('time destination')
    private_time=render_time(previous_header,roots,base_extra,site,msr)
    if shared_edge:private_time=render_shared(private_time,extra,shared_edge[0])
    if frontier:
        call,dst,w=handler_edge(HANDLER,exact(dol,elf,HANDLER,len(roots[HANDLER])),4)
        if call not in guard or call not in reachable(HANDLER,roots[HANDLER],guard,indirect):raise ValueError('transfer frontier geometry')
        candidate,callback_words,callback_sites=callback_expectations(dol,elf)
        private_time=replace_exact(private_time,'#define UNDERCOVER_V975_PRIVATE_TIME 1\n','#define UNDERCOVER_V975_PRIVATE_TIME 1\n#define UNDERCOVER_V981_PRIVATE_FRONTIER 1\n')
        private_time+='namespace undercover::wii::v958 {\n'+f'inline constexpr uint32_t transfer_call=0x{call:08x}u,transfer_branch=0x{w:08x}u,transfer_callback=0x{candidate:08x}u;\n'
        private_time+='inline constexpr uint32_t transfer_data=0x80619a60u,transfer_slots=0x806fe340u;\n}\n'
        header=private.parent/'wii_si_transfer_arguments_v981.h'
        if header.exists() or header.is_symlink():raise ValueError('time destination')
        changes[header]=(Path(__file__).parent/header.name).read_text()
    if success_frontier:
        raw=exact(dol,elf,HANDLER,len(roots[HANDLER]))
        cb=callback_sites[0]
        if cb not in guard or cb not in reachable(HANDLER,roots[HANDLER],guard,indirect) or raw[(cb-HANDLER)//4]!=0x4e800421 or len(callback_words)!=172:raise ValueError('success callback geometry')
        private_time=replace_exact(private_time,'#define UNDERCOVER_V981_PRIVATE_FRONTIER 1\n','#define UNDERCOVER_V981_PRIVATE_FRONTIER 1\n#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1\n')
        fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
        private_time+='namespace undercover::wii::v958 {\n'+f'inline constexpr std::array<uint32_t,172> success_callback_words{{'+fmt(callback_words)+'};\n'
        private_time+='inline constexpr std::array<uint32_t,2> success_callback_sites{'+fmt(callback_sites)+'};\n}\n'
        header=private.parent/'wii_callback_identity_v796.h'
        if header.is_symlink() or not header.is_file() or header.read_text()!=(Path(__file__).parent/header.name).read_text():raise ValueError('success callback identity')
    changes[private]=private_time
    for p,s in changes.items():p.write_text(s)
    print(f'V975_TIME_ROUTE installed=1 native_labels={count} original_edges=7 unchanged_msr_sites=2 execution=0')
    if frontier:print('V981_FRONTIER_ROUTE installed=1 original_call=4 execution=0')
    if shared_edge:print('V989_SHARED_ROUTE installed=1 original_edges=8 shared_time_root=1 execution=0')
    if success_frontier:print('V995_SUCCESS_ROUTE installed=1 direct_boundary=4 indirect_boundary=6 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);p.add_argument('--frontier',action='store_true');p.add_argument('--shared-completion',action='store_true');p.add_argument('--success-frontier',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,a.frontier,a.shared_completion,a.success_frontier)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        allowed=('time shared label','time shared tick','time shared guard','time old hook','time tree','time owner','time destination','transfer frontier geometry','shared time geometry','shared time body','success frontier mode','success callback geometry','success callback identity','source seam','second ACK label','second ACK hook','second ACK tick','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V975_TIME_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
