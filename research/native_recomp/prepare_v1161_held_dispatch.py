#!/usr/bin/env python3
"""Install the fresh third dispatcher using authenticated V951 geometry."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import geometry,render as render_dispatch,exact,DISPATCH,HANDLER,TIME,SCHED,DISABLE,RESTORE
from prepare_owner_second_dispatch_v946 import plan,reachable
from prepare_v1152_held_epilogue import render as render_epilogue,NEW,ACK
from prepare_v1141_postalarm_handler import block_at
from prepare_v1097_after_alarm import SI,ACTIVE,inherited_hooks
from prepare_v1106_postalarm_time import verify_resume
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v1029_third_transfer import replace_body,include_once

DISPATCH_ACTIVE='undercover::wii::v958::held_dispatch_active()'

def patch_label(body,pc,w,root,guard):
    block=block_at(body,pc,w);arg=f'ctx,0x{pc:08x}u,0x{w:08x}u'
    tick='    ++ctx.inst_count;\n';flag=str(guard).lower()
    if block.count(tick)!=1 or block.count(SI)!=1 or block.index(tick)>block.index(SI) or DISPATCH_ACTIVE in block:
        raise ValueError('held dispatcher tick')
    shared=root in (DISABLE,RESTORE,TIME)
    old=(f'undercover::wii::v922::before({arg});' if root in (DISABLE,RESTORE) else
         f'undercover::wii::v922::second_dispatch_before({arg},{flag});')
    plain='    '+old+'\n';gated=f'    if(!{ACK}) '+old+'\n'
    hits=[l for l in block.splitlines(keepends=True) if 'v922::before(' in l or 'v922::second_dispatch_before(' in l]
    if hits!=([gated] if shared else [plain]) or block.index(hits[0])<block.index(SI):
        raise ValueError('held dispatcher legacy')
    current=f'undercover::wii::v958::before({arg},{flag});'
    prior=''.join(re.findall(r'(?m)^    [^\n]*v958::before\(ctx,[^\n]+\n',block))
    if shared:
        # Shared time/disable/restore leaves were already hooked by
        # V975 and V1106. Reuse the existing exact non-guard observer.
        # Guarded shared labels cannot silently become admitted labels.
        if guard:raise ValueError('held dispatcher shared guard')
        verify_resume(body,pc,w)
        if prior not in set(inherited_hooks(pc,w).values())|{f'    if({ACTIVE}) '+current+'\n'} or \
           (prior!='    '+current+'\n' and ACTIVE not in prior):
            raise ValueError('held dispatcher shared')
        return body
    if prior or root not in (DISPATCH,SCHED):
        raise ValueError('held dispatcher shared')
    new=f'    if({DISPATCH_ACTIVE}) '+current+'\n    else '+plain.lstrip()
    if body.count(block)!=1:raise ValueError('held dispatcher block')
    return body.replace(block,block.replace(plain,new,1),1)

def metadata(dol,elf):
    roots,edges,indirect,iw,hw,dw,guard=plan(dol,elf)
    e,site,hword,dword,_=geometry(dol,elf)
    if list(edges)!=list(e) or site!=(indirect,iw) or hword!=hw or dword!=dw:
        raise ValueError('held dispatcher geometry')
    rows={}
    for a,ws in roots.items():
        if a==HANDLER:continue
        original=exact(dol,elf,a,len(ws))
        for pc in reachable(a,ws,guard,indirect):
            if pc in rows:raise ValueError('held dispatcher geometry')
            rows[pc]=(a,original[(pc-a)//4],pc in guard)
    return rows,edges,indirect,hw,render_dispatch(e,site,hw,dw)

def render():
    return ('#pragma once\n#include "v667_private_si_dispatch_expectations.h"\n'
            'namespace undercover::wii::v1158 {\ninline constexpr auto expected=v667::expected;\n}\n')

def install(dol,elf,root,host):
    rows,edges,indirect,hw,prior=metadata(dol,elf)
    dest=root/'nWiiRuntime/include/undercover';private=dest/'v958_private_second_ack.h'
    result=dest/'v1158_private_held_dispatch.h'
    expected={'v667_private_si_dispatch_expectations.h':prior,
              'v1151_private_held_epilogue.h':render_epilogue()}
    for n in ('wii_second_ack_live_v958.h','wii_held_pending_epilogue_v1149.h','wii_third_pending_reentry_v1067.h',
              'wii_second_si_dispatch_v944.h','wii_si_dispatch_v667.h'):
        expected[n]=(host/n).read_text()
    trace=dest/'wii_irq_return_witness_v482.h'
    if dest.is_symlink() or result.exists() or result.is_symlink() or any(
        x.is_symlink() or not x.is_file() for x in (private,trace,*[dest/n for n in expected])):
        raise ValueError('held dispatcher destination')
    if any((dest/n).read_text()!=value for n,value in expected.items()):raise ValueError('held dispatcher identity')
    seam='        si_dispatch_pi_reads.record(write,address,width,value,native);\n        record_second_dispatch_pi(write,address,width,value,native);\n'
    code=trace.read_text()
    if code.count(seam)!=1 or code.count('record_second_dispatch_pi(')!=1:raise ValueError('held dispatcher trace')
    old=private.read_text();macro='#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1\n'
    if old.count(macro)!=1 or 'UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH' in old:raise ValueError('held dispatcher mode')
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(x.is_symlink() or not x.is_file() or x.stat().st_size>64*1024*1024 for x in paths+[main]):
        raise ValueError('held dispatcher tree')
    src={x:x.read_text() for x in paths};outer=main.read_text();changes={}
    all_rows={pc:(a,w) for pc,(a,w,_) in rows.items()};all_rows[HANDLER]=(HANDLER,hw)
    if audit_native(src.values(),outer,all_rows)!=len(all_rows):raise ValueError('held dispatcher coverage')
    def owner(a):
        hits=[p for p,s in src.items() if owns_root(s,a)]
        if len(hits)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('held dispatcher owner')
        return hits[0]
    for a in (DISPATCH,SCHED,TIME,DISABLE,RESTORE,HANDLER):owner(a)
    for a in (DISPATCH,SCHED,TIME,DISABLE,RESTORE):
        p=owner(a);s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        for dst,lr,_,_ in edges:
            if rows.get(lr-4,(0,))[0]==a:verify_direct(body,lr-4,dst)
        if a==DISPATCH:verify_indirect(body,indirect)
        for pc,(rootpc,w,g) in sorted(rows.items()):
            if rootpc==a:
                try:out=patch_label(out,pc,w,a,g)
                except ValueError:
                    print(f'V1161_DISPATCH_HOOK_REFUSAL root={(DISPATCH,SCHED,TIME,DISABLE,RESTORE).index(a)} index={(pc-a)//4} guard={int(g)}')
                    raise
        changes[p]=include_once(replace_body(s,body,out),'#include "undercover/wii_second_ack_live_v958.h"')
    changes[private]=old.replace(macro,macro+'#define UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH 1\n',1)
    changes[result]=render()
    for path,value in changes.items():path.write_text(value)
    print(f'V1161_HELD_DISPATCH_ROUTE installed=1 native_labels={len(rows)} shared_labels={sum(a in (DISABLE,RESTORE,TIME) for a,_,_ in rows.values())} direct_edges=4 indirect=1 trace_reused=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,TypeError,StopIteration) as e:
        safe={'held dispatcher '+s for s in ('geometry','tick','legacy','shared guard','shared','block','destination','identity','trace','mode','tree','coverage','owner')}
        safe|={'postalarm time resume','held handler label','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge','indirect label','indirect LR','indirect dispatch','indirect fallback'}
        print('V1161_HELD_DISPATCH_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
