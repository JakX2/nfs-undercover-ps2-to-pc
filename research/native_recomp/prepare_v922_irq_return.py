#!/usr/bin/env python3
"""Private composition of original scheduler and RFI after V921's real saved frame."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v767_live_epilogue import geometry
from prepare_v616_irq_enable import ENTRY
from prepare_v667_si_dispatch import DISABLE,RESTORE
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v850_callback_return import BLOCK_END,INSTR_PREFIX
from prepare_v807_callback_prefix import SI

def patch_label(body,pc,w,resume=False,shared=0):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('IRQ return label')
    m=hits[0];tail=body[m.end():];tick=r'    \+\+ctx\.inst_count;\n'
    if resume:
        # Require the exact existing V616 pre-label trace, which observes
        # the outer dispatcher tick on return from the real RFI.
        tick=r'    if \(nwii::runtime::g_trace_calls\) nwii::runtime::trace_call\(0x'+f'{pc:X}'+r', ctx\); // V616 native IRQ resume\n'+tick
    hit=re.match(tick,tail,re.I)
    if not hit:raise ValueError('IRQ return tick')
    start=m.end()+hit.end();end_match=BLOCK_END.search(body,start)
    end=end_match.start() if end_match else len(body);block=body[start:end]
    if block.count(SI)!=1 or 'v922::' in block or not INSTR_PREFIX.fullmatch(block[:block.index(SI)]):
        raise ValueError('IRQ return scheduler')
    if shared:
        if shared not in (1,3) or resume:raise ValueError('IRQ return shared leaf')
        old=f'    undercover::wii::v709::before(ctx,0x{pc:08x}u,0x{w:08x}u,{shared}u);\n'
        if block.count(old)!=1 or block.index(old)<block.index(SI):
            raise ValueError('IRQ return shared leaf')
        block=replace_exact(block,old,'    if(!undercover::wii::v922::active()) '+old.lstrip())
    elif 'undercover::wii::v709::before(' in block:
        raise ValueError('IRQ return shared leaf')
    pos=block.index(SI)+len(SI);name='resume' if resume else 'before'
    block=block[:pos]+f'    undercover::wii::v922::{name}(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+block[pos:]
    return body[:start]+block+body[end:]

def patch_entry(s):
    a='#include "wii_saved_context_join_v921.h"'
    s=replace_exact(s,a,a+'\n#include "wii_live_irq_return_binding_v922.h"')
    a='    if(v667::route.stage())return v667::poll(c);'
    s=replace_exact(s,a,'    if(v922::active())return v922::poll(c);\n'+a)
    a='    if(v667::route.stage()){v667::observe(a,c);return;}'
    return replace_exact(s,a,'    if(v922::active()){v922::observe(a,c);return;}\n'+a)

def patch_return(s):
    a='#include "wii_saved_context_join_v921.h"'
    s=replace_exact(s,a,a+'\n#include "wii_live_irq_return_binding_v922.h"')
    a='    std::cout<<"V921_SAVED_CONTEXT_RETURN original_snapshot=1 saved_gprs=32 special=6 same_cpu=1 unchanged=1 rfi_return=0 boot_verified=0"<<std::endl;\n    std::_Exit(0);'
    return replace_exact(s,a,a.replace('std::_Exit(0);','v922::begin(c,pc,w);'))

def install(dol,elf,root,host):
    expected,j,resume,header,edges,entries=geometry(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('IRQ return tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();verify_resume_dispatch(outer,ENTRY,resume)
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('IRQ return coverage')
    def owner(a):
        found=[p for p,s in src.items() if owns_root(s,a)]
        if len(found)!=1:raise ValueError('IRQ return owner')
        return found[0]
    for a,links in edges:
        body=exact_function(src[owner(a)],a)
        for pc,dst in links:verify_direct(body,pc,dst)
    if any(sum(entry_count(s,a) for s in src.values())!=1 for a in entries):raise ValueError('IRQ return entries')
    changes={}
    for a in sorted({a for a,_ in expected.values()}):
        p=owner(a);s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        for pc,(rootpc,w) in sorted(expected.items()):
            if a==rootpc and pc!=j:out=patch_label(out,pc,w,pc==resume,1 if a==DISABLE else 3 if a==RESTORE else 0)
        if out==body:raise ValueError('IRQ return coverage')
        s=replace_exact(s,body,out)
        inc='#include "undercover/wii_live_irq_return_binding_v922.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_live_epilogue_v762.h','wii_live_irq_return_binding_v922.h','wii_pending_external_reentry_v932.h')}
    files[dest/'v922_private_irq_return.h']=header.replace('::v767','::v922')
    a=dest/'wii_external_entry_binding_v663.h';b=dest/'wii_handler_suffix_binding_v868.h'
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() or not p.is_file() for p in (a,b)):
        raise ValueError('IRQ return destination')
    files[a]=patch_entry(a.read_text());files[b]=patch_return(b.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print(f'V922_IRQ_RETURN_ROUTE installed=1 native_labels={len(expected)} same_thread=1 exact_resume=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('IRQ return shared leaf','IRQ return label','IRQ return tick','IRQ return scheduler','IRQ return tree','IRQ return owner','IRQ return entries','IRQ return coverage','IRQ return destination','source seam','native IPC label identity','native IPC coverage','native IPC dispatch','native IPC duplicate root','resume dispatcher identity','helper call label','helper direct native call','helper native return edge')
        print('V922_IRQ_RETURN_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
