#!/usr/bin/env python3
"""Privately install the held handler's native restore and dispatcher resume."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import HANDLER
from prepare_v667_si_dispatch import DISPATCH,geometry,exact
from prepare_v868_handler_suffix import derive
from prepare_v1141_postalarm_handler import render as render_suffix,block_at,patch_handler
from prepare_owner_handler_tail_v879 import plan
from prepare_v738_handler_restore import audit_shared_alias
from prepare_v1097_after_alarm import ACTIVE,SI,fmt,patch_label
from prepare_v1106_postalarm_time import verify_resume
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v625_ipc_client import audit_native
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v1029_third_transfer import replace_body,include_once

def render(call,root,resume,restore,tail,w):
    return ('#pragma once\n#include "wii_callback_return_v846.h"\nnamespace undercover::wii::v1145 {\n'
            'inline constexpr HandlerReturnExpectation expected{'+fmt((call,root,resume))+',{'
            +fmt(restore)+'},{'+fmt(tail)+'},'+fmt((w,))+'};\n}\n')

def geometry_return(dol,elf):
    q,_,_=plan(dol,elf);roots,call,root,_,base,disp=q
    _,(site,_),_,_,_=geometry(dol,elf)
    resume=site+4;w=exact(dol,elf,resume,1)[0]
    restore=roots[root];tail=roots[call][1:];branch=roots[call][0]
    if len(restore)!=16 or len(tail)!=4 or restore[-1]!=0x4e800020 or tail[-1]!=0x4e800020:
        raise ValueError('held return geometry')
    h='#pragma once\n#include "wii_gpr_restore_v736.h"\nnamespace undercover::wii::v868 {\n'
    h+=f'inline constexpr GprRestoreExpectation restore_expected{{0x{call:08x}u,0x{root:08x}u,0x{branch:08x}u,17u,{base}u,{disp}}};\n'
    h+='inline constexpr std::array<HandlerSuffixLabel,4> epilogue_labels{{'
    h+=','.join(f'HandlerSuffixLabel{{0x{call+4+4*i:08x}u,0x{x:08x}u,0u,0u}}' for i,x in enumerate(tail))+'}};\n}\n'
    d='#pragma once\n#include <cstdint>\nnamespace undercover::wii::v868 {\n'
    d+=f'inline constexpr uint32_t dispatcher_resume_pc=0x{resume:08x}u,dispatcher_resume_word=0x{w:08x}u;\n}}\n'
    return call,root,resume,restore,tail,w,branch,h,d

def exact_hook(block,hook):
    if block.count(hook)!=1:raise ValueError('held return legacy')
    return hook

def replace_block(body,old,new):
    if body.count(old)!=1:raise ValueError('held return block')
    return body.replace(old,new,1)

def patch_restore(body,pc,w):
    block=block_at(body,pc,w);a=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    legacy=f'    undercover::wii::v868::restore_before({a});\n'
    if block.count('v868::restore_before(')!=1 or block.count(SI)!=1 or block.index(SI)>block.index(exact_hook(block,legacy)):
        raise ValueError('held return legacy')
    old=f'    if(!undercover::wii::v868::active()) undercover::wii::v726::restore_before({a});\n'
    if block.count('v726::restore_before(')>1 or ('v726::restore_before(' in block and block.count(old)!=1):
        raise ValueError('held return legacy')
    out=patch_label(body,pc,w);updated=block_at(out,pc,w)
    updated2=updated.replace(legacy,f'    if(!{ACTIVE}) '+legacy.lstrip(),1)
    if old in updated2:updated2=updated2.replace(old,f'    if(!{ACTIVE}) {{ '+old.strip()+' }\n',1)
    out=replace_block(out,updated,updated2);verify_resume(out,pc,w)
    return out

def patch_dispatch(body,pc,w):
    block=block_at(body,pc,w);a=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    pre=f'    undercover::wii::v868::dispatch_resume({a});\n'
    post=f'    undercover::wii::v868::dispatcher_resume({a});\n'
    old=f'    if(!undercover::wii::v868::return_active()) undercover::wii::v726::resume({a});\n'
    tick='    ++ctx.inst_count;\n'
    if not block.startswith(pre+tick) or any(block.count(x)!=1 for x in (pre,post,old,SI,tick)) or \
       not block.index(tick)<block.index(old)<block.index(SI)<block.index(post) or \
       any(block.count(x)!=1 for x in ('v868::dispatch_resume(','v868::dispatcher_resume(','v726::resume(')):
        raise ValueError('held return dispatcher')
    # patch_label adds one post-SI observer and suppresses the exact V726
    # legacy seam. The old V868 observer must also be disabled on both sides
    # of the tick while the new held token owns the return.
    out=patch_label(body,pc,w);updated=block_at(out,pc,w)
    newpre=f'    if(!{ACTIVE}) '+pre.lstrip()+f'    undercover::wii::v958::postalarm_handler_dispatch_resume({a});\n'
    updated2=updated.replace(pre,newpre,1).replace(post,f'    if(!{ACTIVE}) '+post.lstrip(),1)
    if f'    if(!{ACTIVE}) {{ '+old.strip()+' }\n' not in updated2:
        raise ValueError('held return legacy')
    out=replace_block(out,updated,updated2);verify_resume(out,pc,w)
    return out

def install(dol,elf,root,host):
    call,R,resume,restore,tail,w,branch,h,d=geometry_return(dol,elf)
    _,sites,lanes,rd,wr,index=derive(dol,elf);rows=lanes[0]
    if len(rows)!=52 or rows.get(call)!=(branch,12,1) or set(rows)&{call+4+4*i for i in range(4)}:
        raise ValueError('held return geometry')
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    result=dest/'v1145_private_postalarm_handler_return.h'
    expected={'v1139_private_postalarm_handler.h':render_suffix(rows,rd,wr,index),
              'v919_private_handler_epilogue.h':h,'v920_private_handler_resume.h':d}
    for name in ('wii_third_alarm_suffix_v1047.h','wii_callback_return_v846.h','wii_second_ack_live_v958.h'):
        expected[name]=(host/name).read_text()
    if dest.is_symlink() or result.exists() or result.is_symlink() or any(
        x.is_symlink() or not x.is_file() for x in (private,*[dest/n for n in expected])):
        raise ValueError('held return destination')
    if any((dest/n).read_text()!=value for n,value in expected.items()):raise ValueError('held return identity')
    old=private.read_text();macro='#define UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN' in old:
        raise ValueError('held return mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('held return tree')
    src={x:x.read_text() for x in paths};outer=main.read_text();changes={}
    def owner(a):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('held return owner')
        return hits[0]
    if audit_shared_alias(src.values(),outer,R,restore)!=16:raise ValueError('held return coverage')
    verify_resume_dispatch(outer,DISPATCH,resume)
    for a,labels in ((HANDLER,{call+4+4*i:x for i,x in enumerate(tail)}),
                     (R,{R+4*i:x for i,x in enumerate(restore)}),(DISPATCH,{resume:w})):
        p=owner(a);source=changes.get(p,src[p]);body=exact_function(source,a);out=body
        check={pc:(a,x) for pc,x in labels.items()}
        if a==HANDLER:
            verify_direct(body,call,R);verify_resume(body,call,branch);check[call]=(a,branch)
        if audit_native([body],outer,check)!=len(check):raise ValueError('held return coverage')
        for pc,x in labels.items():
            if a==R:out=patch_restore(out,pc,x)
            elif a==DISPATCH:out=patch_dispatch(out,pc,x)
            else:out=patch_handler(out,pc,x,0,0,sites[0]+4)
        changes[p]=include_once(replace_body(source,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    changes[private]=old.replace(macro,macro+'#define UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN 1\n',1)
    changes[result]=render(call,R,resume,restore,tail,w)
    for path,value in changes.items():path.write_text(value)
    print('V1146_POSTALARM_HANDLER_RETURN_ROUTE installed=1 restore_labels=16 tail_labels=4 dispatcher_resume=1 outer_tick=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,TypeError,StopIteration) as e:
        safe={'held return '+s for s in ('geometry','legacy','block','dispatcher','destination','identity','mode','tree','owner','coverage')}
        safe|={'postalarm label','postalarm tick','postalarm hook','postalarm duplicate','postalarm time resume',
               'native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','resume dispatcher identity',
               'held handler label','held handler legacy','held handler resume'}
        print('V1146_POSTALARM_HANDLER_RETURN_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
