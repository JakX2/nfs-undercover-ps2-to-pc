#!/usr/bin/env python3
"""Private held-third-token post-time callback frontier installer."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_callback_frontier_v820 import plan
from prepare_v831_callback_frontier import render
from prepare_v813_callback_time import render as render_time
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from prepare_v1097_after_alarm import patch_label,fmt
from prepare_v1106_postalarm_time import verify_resume
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v1029_third_transfer import replace_body,include_once

def install(dol,elf,root,host):
    q,seen,stops,A,B=plan(dol,elf)
    base,T,D,U,R,ts,leaves=q;roots,C,S,site,_,_=base
    original=exact(dol,elf,C,172);candidate,words,_=expectations(dol,elf)
    resume=ts+4
    if candidate!=C or tuple(original)!=tuple(words) or len(original)!=172 or \
       len(seen)!=27 or len(set(seen))!=27 or resume not in seen or min(seen)!=resume or \
       sorted(o for o,_ in stops.values())!=[3,5] or set(dst for _,dst in stops.values())!={A,B} or \
       not set(stops).issubset(seen) or A==B or any(pc&3 or not resume<=pc<C+688 for pc in seen):
        raise ValueError('postalarm frontier geometry')
    expected={pc:(C,original[(pc-C)//4]) for pc in seen}
    dest=root/'nWiiRuntime/include/undercover'
    private=dest/'v958_private_second_ack.h';time=dest/'v813_private_callback_time.h'
    frontier=dest/'v831_private_callback_frontier.h'
    witnesses=('wii_callback_frontier_v829.h','wii_third_alarm_suffix_v1047.h','wii_callback_time_v810.h')
    if dest.is_symlink() or any(x.is_symlink() or not x.is_file() for x in (private,time,frontier,*[dest/n for n in witnesses])):
        raise ValueError('postalarm frontier destination')
    continuation=original[(site+4-C)//4:(ts+4-C)//4+1]
    if time.read_text()!=render_time(C,ts,continuation,T,roots[T],leaves) or \
       frontier.read_text()!=render(C,resume,expected,stops) or \
       any((dest/n).read_text()!=(host/n).read_text() for n in witnesses):
        raise ValueError('postalarm frontier identity')
    old=private.read_text();macro='#define UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME 1\n'
    newmacro='#define UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER' in old:
        raise ValueError('postalarm frontier mode')
    row=f'inline constexpr std::array<uint32_t,{len(words)}> third_postalarm_words{{'+fmt(words)+'};\n'
    if old.count(row)!=1 or len(re.findall(r'\btransfer_callback\s*=\s*0x'+f'{C:08x}'+r'u\b',old,re.I))!=1:
        raise ValueError('postalarm frontier metadata')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('postalarm frontier tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    owners=[p for p,s in src.items() if owns_root(s,C)]
    if len(owners)!=1 or sum(entry_count(s,C) for s in src.values())!=1:
        raise ValueError('postalarm frontier owner')
    path=owners[0];source=src[path];body=exact_function(source,C);out=body
    for pc,(_,dst) in sorted(stops.items()):verify_direct(body,pc,dst)
    if audit_native([body],outer,expected)!=len(expected):raise ValueError('postalarm frontier coverage')
    for pc,(_,w) in sorted(expected.items()):
        if pc==resume:verify_resume(out,pc,w)
        else:out=patch_label(out,pc,w)
    updated=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    path.write_text(updated);private.write_text(old.replace(macro,macro+newmacro,1))
    print('V1113_POSTALARM_FRONTIER_ROUTE installed=1 callback_labels=27 direct_edges=2 resume_reused=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        safe=('postalarm frontier geometry','postalarm frontier destination','postalarm frontier identity',
              'postalarm frontier mode','postalarm frontier metadata','postalarm frontier tree','postalarm frontier owner',
              'postalarm frontier coverage','postalarm time resume','postalarm label','postalarm tick','postalarm duplicate',
              'postalarm hook','helper call label','helper direct native call','helper native return edge',
              'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch')
        print('V1113_POSTALARM_FRONTIER_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
