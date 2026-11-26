#!/usr/bin/env python3
"""Authenticate private native held-token wireless setter continuation."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_callback_frontier_v820 import plan as frontier_plan
from prepare_owner_wireless_v816 import plan as wrapper_plan
from prepare_v847_wireless_wrapper import render
from prepare_v831_callback_frontier import render as render_frontier
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE
from prepare_v789_alarm_suffix import expectations
from prepare_v1097_after_alarm import patch_label,fmt
from prepare_v1106_postalarm_time import verify_resume
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v1029_third_transfer import replace_body,include_once
from prepare_owner_scheduler_v722 import reachable
from audit_callback_frontiers_v799 import call_sites

def install(dol,elf,root,host):
    q,seen,stops,A,B=frontier_plan(dol,elf)
    base,T,D,TB,R,ts,leaves=q;time_roots,C,S,site,_,_=base
    roots,a,b,U,L,guards=wrapper_plan(dol,elf)
    original=exact(dol,elf,C,172);candidate,words,_=expectations(dol,elf)
    if candidate!=C or tuple(original)!=tuple(words) or len(original)!=172 or \
       (A,B)!=(a,b) or (D,R)!=(DISABLE,RESTORE) or len(seen)!=27 or len(set(seen))!=27 or \
       sorted(o for o,_ in stops.values())!=[3,5] or set(dst for _,dst in stops.values())!={A,B} or \
       not set(stops).issubset(seen) or any(pc&3 or not ts+4<=pc<C+684 for pc in seen):
        raise ValueError('postalarm wireless geometry')
    order=(A,B,U,D,R)
    if len(set(order))!=5 or L in order or [len(roots[x]) for x in order]!=[39,30,184,5,9] or \
       any(tuple(roots[x])!=tuple(time_roots[x]) for x in (D,R)):
        raise ValueError('postalarm wireless extent')
    edges=[(pc,original[(pc-C)//4],original[(pc+4-C)//4],o) for pc,(o,_) in sorted(stops.items())]
    lw=exact(dol,elf,L,1)[0]
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    frontier=dest/'v831_private_callback_frontier.h';wireless=dest/'v847_private_wireless_wrapper.h'
    witnesses=('wii_callback_frontier_v829.h','wii_wireless_wrapper_v844.h','wii_third_alarm_suffix_v1047.h')
    if dest.is_symlink() or any(p.is_symlink() or not p.is_file() for p in (private,frontier,wireless,*[dest/n for n in witnesses])):
        raise ValueError('postalarm wireless destination')
    expected={pc:(C,original[(pc-C)//4]) for pc in seen}
    if frontier.read_text()!=render_frontier(C,ts+4,expected,stops) or \
       wireless.read_text()!=render(roots,order,edges,L,lw) or \
       any((dest/n).read_text()!=(host/n).read_text() for n in witnesses):
        raise ValueError('postalarm wireless identity')
    old=private.read_text();macro='#define UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER 1\n'
    newmacro='#define UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS' in old:
        raise ValueError('postalarm wireless mode')
    row=f'inline constexpr std::array<uint32_t,{len(words)}> third_postalarm_words{{'+fmt(words)+'};\n'
    if old.count(row)!=1 or len(re.findall(r'\btransfer_callback\s*=\s*0x'+f'{C:08x}'+r'u\b',old,re.I))!=1:
        raise ValueError('postalarm wireless metadata')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('postalarm wireless tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={}
    def owner(x):
        hits=[p for p,s in src.items() if owns_root(s,x)]
        if len(hits)!=1 or sum(entry_count(s,x) for s in src.values())!=1:
            raise ValueError('postalarm wireless owner')
        return hits[0]
    def rewrite(x,rows,reuse,edges):
        p=owner(x);s=changes.get(p,src[p]);body=exact_function(s,x);out=body
        for pc,target in edges:verify_direct(body,pc,target)
        if audit_native([body],outer,rows)!=len(rows):raise ValueError('postalarm wireless coverage')
        for pc,(_,w) in sorted(rows.items()):
            if pc in reuse:verify_resume(out,pc,w)
            else:out=patch_label(out,pc,w)
        if out!=body:changes[p]=include_once(replace_body(s,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    p=owner(L);body=exact_function(src[p],L)
    if audit_native([body],outer,{L:(L,lw)})!=1:raise ValueError('postalarm wireless coverage')
    labels=shared=direct=0
    for x in order:
        rows={pc:(x,roots[x][(pc-x)//4]) for pc in reachable(x,roots[x])}
        calls=call_sites(x,roots[x])
        if any(k!=1 or target not in roots for _,k,target in calls):
            raise ValueError('postalarm wireless edge')
        reuse=set(rows) if x in (D,R) else set()
        rewrite(x,rows,reuse,[(pc,target) for pc,_,target in calls])
        labels+=len(rows);shared+=len(reuse);direct+=len(calls)
    # Verify both call sites were already hooked. A return label may also
    # belong to the earlier frontier; never install a second live hook.
    callbacks={pc:(C,original[(pc-C)//4]) for pc in set(stops)|{pc+4 for pc in stops}}
    reuse=set(callbacks)&set(seen)
    rewrite(C,callbacks,reuse,[(pc,dst) for pc,(_,dst) in stops.items()])
    changes[private]=old.replace(macro,macro+newmacro,1)
    for p,s in changes.items():p.write_text(s)
    print(f'V1119_POSTALARM_WIRELESS_ROUTE installed=1 wrapper_labels={labels} shared_labels={shared} direct_edges={direct+2} callback_returns=2 lock_entry=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        safe=('postalarm wireless geometry','postalarm wireless extent','postalarm wireless destination',
              'postalarm wireless identity','postalarm wireless mode','postalarm wireless metadata','postalarm wireless tree',
              'postalarm wireless owner','postalarm wireless coverage','postalarm wireless edge','postalarm time resume',
              'postalarm label','postalarm tick','postalarm duplicate','postalarm hook','helper call label',
              'helper direct native call','helper native return edge','native IPC label identity','native IPC label body',
              'native IPC coverage','native IPC dispatch')
        print('V1119_POSTALARM_WIRELESS_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
