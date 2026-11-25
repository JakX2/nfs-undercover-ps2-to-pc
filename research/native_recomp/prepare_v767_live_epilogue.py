#!/usr/bin/env python3
"""Private exact native dispatcher/OSLoadContext continuation after handler return."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_epilogue_v737 import plan
from prepare_owner_scheduler_v722 import E,S,reachable
from prepare_owner_context_v720 import L
from prepare_v667_si_dispatch import DISPATCH,exact
from prepare_v616_irq_enable import expectations,ENTRY
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v726_handler_return import verify_resume_dispatch
def geometry(dol,elf):
    roots,j,reg,gqr,counter,hint,D,R,G,calls=plan(dol,elf)
    _,resume,labels=expectations(dol,elf)
    expected={j+4*i:(DISPATCH,w) for i,w in enumerate(roots[j][:4])}
    for a in (E,S,D,R,L):
        ws=roots[a]
        for pc in (range(a,a+4*len(ws),4) if a==L else reachable(a,ws)):
            if pc in expected:raise ValueError('overlap')
            expected[pc]=(a,ws[(pc-a)//4])
    expected[resume]=(ENTRY,labels[resume])
    header='#pragma once\n#include "wii_live_epilogue_v762.h"\nnamespace undercover::wii::v767 {\n'
    header+='inline constexpr LiveEpilogueExpectation expected{'+','.join(f'0x{x:08x}u' for x in (j,E,S,D,R,L,G,0x806f5318))+f',{counter},{hint},{reg}u,{gqr}u'+'};\n'
    header+=f'inline constexpr uint32_t resume_pc=0x{resume:08x}u,resume_word=0x{labels[resume]:08x}u;\n'+'}\n'
    return expected,j,resume,header,((DISPATCH,[(j,E),(j+4,S),(j+12,L)]),(E,calls)),(E,S,D,R,L)
def patch_entry(s):
    a='#include "wii_cold_return_capture_v741.h"'
    s=replace_exact(s,a,a+'\n#include "wii_live_epilogue_binding_v767.h"')
    a='    if(v667::route.stage())return v667::poll(c);'
    s=replace_exact(s,a,'    if(v767::active())return v767::poll(c);\n'+a)
    a='    if(v667::route.stage()){v667::observe(a,c);return;}'
    s=replace_exact(s,a,'    if(v767::active()){v767::observe(a,c);return;}\n'+a)
    a='            std::cout<<"V751_CAPTURE_STAGE n=2"'
    return replace_exact(s,a,'            v767::attach(capture.witness());\n'+a)
def patch_handler(s):
    a='#include "wii_si_handler_return_v725.h"'
    s=replace_exact(s,a,a+'\n#include "wii_live_epilogue_binding_v767.h"')
    a='    std::_Exit(0);\n}\n}'
    return replace_exact(s,a,'    if(v767::begin(c,pc,w))return;\n'+a)
def patch_label(s,pc,w,resume):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    m=list(pat.finditer(s))
    if len(m)!=1:raise ValueError('label identity')
    # The original IRQ resume already has a V616 pre-tick trace hook.
    # Preserve that trace, then verify immediately after the real tick.
    tail=s[m[0].end():]
    tick=r'    \+\+ctx\.inst_count;\n'
    if resume:
        tick=r'(?:    if \(nwii::runtime::g_trace_calls\) nwii::runtime::trace_call\(0x'+f'{pc:X}'+r', ctx\); // V616 native IRQ resume\n)?'+tick
    hit=re.match(tick,tail,re.I)
    if not hit:raise ValueError('tick identity')
    end=m[0].end()+hit.end()
    name='resume' if resume else 'before'
    return s[:end]+f'    undercover::wii::v767::{name}(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+s[end:]
def install(dol,elf,root,host):
    expected,j,resume,header,edges,entries=geometry(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('private tree')
    outer=main.read_text();verify_resume_dispatch(outer,ENTRY,resume)
    sources={p:p.read_text() for p in paths}
    if audit_native(sources.values(),outer,expected)!=len(expected):raise ValueError('native coverage')
    for owner,links in edges:
        owners=[exact_function(s,owner) for s in sources.values() if owns_root(s,owner)]
        if len(owners)!=1:raise ValueError('call owner')
        for site,dst in links:verify_direct(owners[0],site,dst)
    if any(sum(entry_count(s,a) for s in sources.values())!=1 for a in entries):raise ValueError('entry coverage')
    changes={};seen=set()
    for p,old in sources.items():
        s=old
        for pc,(_,w) in expected.items():
            if pc==j or not re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s):continue
            if pc in seen:raise ValueError('duplicate label')
            s=patch_label(s,pc,w,pc==resume);seen.add(pc)
        if s!=old:
            a='#include "runtime/cpu_context.h"'
            changes[p]=replace_exact(s,a,a+'\n#include "undercover/wii_live_epilogue_binding_v767.h"')
    if seen!=set(expected)-{j}:raise ValueError('hook coverage')
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_live_epilogue_v762.h','wii_live_epilogue_binding_v767.h')}
    files[dest/'v767_private_epilogue_expectations.h']=header
    edits={dest/'wii_external_entry_binding_v663.h':patch_entry,dest/'wii_si_handler_return_binding_v726.h':patch_handler}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() for p in edits):raise ValueError('destination')
    for p,fn in edits.items():files[p]=fn(p.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print(f'V767_EPILOGUE_ROUTE installed=1 native_labels={len(expected)} exact_resume=1 guarded_switch=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        safe=('overlap','private tree','native coverage','call owner','entry coverage','duplicate label','label identity','tick identity','hook coverage','destination','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','resume dispatcher identity','helper call label','helper direct native call','helper native return edge')
        print('V767_EPILOGUE_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
