#!/usr/bin/env python3
"""Private continuation from the held third callback prefix through OS time."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_callback_time_v802 import plan
from prepare_v813_callback_time import render
from prepare_v807_callback_prefix import render as prefix_render,SI
from prepare_v789_alarm_suffix import expectations
from prepare_v667_si_dispatch import exact
from prepare_owner_scheduler_v722 import reachable
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v850_callback_return import BLOCK_END
from prepare_v1029_third_transfer import replace_body,include_once
from prepare_v1097_after_alarm import patch_label,ACTIVE,OLD_ACTIVE,CALLBACK,OLD_SUPPRESS,fmt,LEGACY

def verify_resume(body,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('postalarm time resume')
    i=hits[0].end();end=BLOCK_END.search(body,i);block=body[i:end.start() if end else len(body)]
    tick='++ctx.inst_count;'
    if block.count(SI)!=1 or block.count(tick)!=1 or block.index(tick)>block.index(SI):
        raise ValueError('postalarm time resume')
    base=f'undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,'
    current='    '+base+'false);\n';guard='    '+base+'true);\n'
    cond=lambda name:'    if('+name+') '+current.lstrip()
    allowed={current,cond(ACTIVE),cond(ACTIVE)+'    else '+guard.lstrip()}
    for prior in (CALLBACK,OLD_ACTIVE,OLD_ACTIVE+'||'+CALLBACK):
        allowed.add(cond(prior+'||'+ACTIVE))
    allowed.add(cond(OLD_ACTIVE+'||'+ACTIVE)+'    else '+guard.lstrip())
    observed=''.join(re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block))
    if observed not in allowed or block.count(observed)!=1 or block.index(observed)<block.index(SI) or OLD_SUPPRESS in block or LEGACY.search(block):
        raise ValueError('postalarm time resume')

def install(dol,elf,root,host):
    q,T,D,U,R,ts,leaves=plan(dol,elf);roots,C,S,site,_,_=q
    resume=site+4;prefix=roots[C][:(resume-C)//4+1];save=roots[S]
    candidate,words,sites=expectations(dol,elf)
    continuation=roots[C][(resume-C)//4:-1]
    original=exact(dol,elf,C,172)
    if candidate!=C or len(prefix)!=6 or len(save)!=7 or len(words)!=172 or len(sites)!=2 or \
       tuple(original)!=tuple(words) or tuple(roots[C][:-1])!=tuple(original[:(ts-C)//4+2]) or \
       tuple(continuation)!=tuple(original[(resume-C)//4:(ts-C)//4+2]) or len(roots[T])!=25:
        raise ValueError('postalarm time geometry')
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    prefix_header=dest/'v807_private_callback_prefix.h';time_header=dest/'v813_private_callback_time.h'
    witnesses=('wii_callback_prefix_v800.h','wii_callback_time_v810.h','wii_third_alarm_suffix_v1047.h')
    if dest.is_symlink() or any(x.is_symlink() or not x.is_file() for x in (private,prefix_header,time_header,*[dest/n for n in witnesses])):
        raise ValueError('postalarm time destination')
    if prefix_header.read_text()!=prefix_render(C,S,prefix,save) or time_header.read_text()!=render(C,ts,continuation,T,roots[T],leaves) or \
       any((dest/n).read_text()!=(host/n).read_text() for n in witnesses):
        raise ValueError('postalarm time identity')
    old=private.read_text();macro='#define UNDERCOVER_V1095_PRIVATE_AFTER_ALARM 1\n'
    newmacro='#define UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME' in old:
        raise ValueError('postalarm time mode')
    rows=[f'inline constexpr uint32_t third_postalarm_save_root=0x{S:08x}u;\n']
    for name,ws in (('third_postalarm_prefix',prefix),('third_postalarm_save',save),('third_postalarm_words',words),('third_postalarm_sites',sites)):
        rows.append(f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+fmt(ws)+'};\n')
    if any(old.count(row)!=1 for row in rows) or len(re.findall(r'\btransfer_callback\s*=\s*0x'+f'{C:08x}'+r'u\b',old,re.I))!=1:
        raise ValueError('postalarm time metadata')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('postalarm time tree')
    src={x:x.read_text() for x in paths};outer=main.read_text();changes={}
    def owner(addr):
        hits=[x for x,s in src.items() if owns_root(s,addr)]
        if len(hits)!=1 or sum(entry_count(s,addr) for s in src.values())!=1:
            raise ValueError('postalarm time owner')
        return hits[0]
    pcs={pc for pc in reachable(C,roots[C]) if resume<=pc<=ts+4}
    if len(pcs)!=13 or resume not in pcs or ts+4 not in pcs:raise ValueError('postalarm time geometry')
    total=0
    for addr in (C,T,D,U,R):
        p=owner(addr);source=changes.get(p,src[p]);body=exact_function(source,addr);out=body
        labels=pcs if addr==C else reachable(addr,roots[addr])
        for a,t in ([(ts,T)] if addr==C else [(x[0],x[1]) for x in leaves] if addr==T else []):
            verify_direct(body,a,t)
        expected={pc:(addr,roots[addr][(pc-addr)//4]) for pc in labels}
        if audit_native([body],outer,expected)!=len(expected):raise ValueError('postalarm time coverage')
        for pc,(_,w) in sorted(expected.items()):
            if pc==resume:verify_resume(out,pc,w)
            else:out=patch_label(out,pc,w)
        changes[p]=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
        total+=len(expected)
    if total-len(pcs)!=45:raise ValueError('postalarm time geometry')
    changes[private]=old.replace(macro,macro+newmacro,1)
    for p,s in changes.items():p.write_text(s)
    print('V1106_POSTALARM_TIME_ROUTE installed=1 callback_labels=13 shared_labels=45 direct_edges=4 resume_reused=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        safe=('postalarm time resume','postalarm time geometry','postalarm time destination','postalarm time identity',
              'postalarm time mode','postalarm time metadata','postalarm time tree','postalarm time owner','postalarm time coverage',
              'postalarm label','postalarm tick','postalarm duplicate','postalarm hook','helper call label','helper direct native call',
              'helper native return edge','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch')
        print('V1106_POSTALARM_TIME_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
