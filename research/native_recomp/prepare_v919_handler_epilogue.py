#!/usr/bin/env python3
"""Owner-only admission of the original ordinal-12 restore and terminal epilogue."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_owner_restore_v735 import plan
from prepare_v672_si_ack_route import call_census
from prepare_v868_handler_suffix import verify_handler_label
from prepare_v738_handler_restore import audit_shared_alias
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v850_callback_return import LABEL_TICK,BLOCK_END,INSTR_PREFIX,RESTORE_HOOK
from prepare_v807_callback_prefix import SI
from audit_handler_suffix_v728 import suffix
from prepare_v625_ipc_client import audit_native

def epilogue(root,words,site):
    n,backs,stores,stops=suffix(root,words,site+4)
    if not 1<=n<=12 or backs or stores or stops!=[(site+4*n,3,0,None)]:
        raise ValueError('epilogue geometry')
    rows=[(site+4*i,words[(site-root)//4+i]) for i in range(1,n+1)]
    if any(w>>26 in (16,17,18,19) for _,w in rows[:-1]):
        raise ValueError('epilogue control')
    return rows

def patch_alias(body,root,code):
    for i,w in enumerate(code):
        pc=root+4*i
        hits=list(LABEL_TICK(pc,w).finditer(body))
        if len(hits)!=1:raise ValueError('restore label identity')
        m=hits[0];start=m.end();stop=BLOCK_END.search(body,start)
        end=stop.start() if stop else len(body);block=body[start:end]
        if block.count(SI)!=1 or not INSTR_PREFIX.fullmatch(block[:block.index(SI)]):
            raise ValueError('restore scheduler')
        if 'v868::restore_before' in block or len(list(RESTORE_HOOK.finditer(block)))>1:
            raise ValueError('restore hook')
        block=RESTORE_HOOK.sub(lambda h:'    if(!undercover::wii::v868::active()) '+h[0].lstrip(),block)
        pos=block.index(SI)+len(SI)
        block=block[:pos]+f'    undercover::wii::v868::restore_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+block[pos:]
        body=body[:start]+block+body[end:]
    return body

def patch_binding(s):
    s=replace_exact(s,'#include "v868_private_handler_suffix.h"','#include "v868_private_handler_suffix.h"\n#include "v919_private_handler_epilogue.h"')
    s=replace_exact(s,'inline bool active(){return lane!=0u;}','''inline bool active(){return lane!=0u;}
inline thread_local GprRestoreWitness restore(restore_expected);
inline thread_local HandlerSuffixGuard epilogue_guard;
inline bool restore_enabled(){const char* v=std::getenv("UNDERCOVER_V919_HANDLER_EPILOGUE");return v&&v[0]=='1'&&v[1]=='\\0';}''')
    a='template<class C>bool before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){'
    s=replace_exact(s,a,'''template<class C>bool advance_restore(C& c){
    return si_transfer_device.after_return_at(c.inst_count)&&
        (!v861::active()||v861::device.observe(c.inst_count))&&v850::held(c);
}
template<class C>void observe(uint32_t pc,C& c){
    if(!restore_enabled()||restore.stage()!=1u||!v850::held(c)||!restore.entry(c,pc))reject(6);
    std::cout<<"V919_RESTORE_ENTRY original_target=1"<<std::endl;
}
template<class C>void restore_before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!restore_enabled()||restore.stage()!=2u||!advance_restore(c)||!restore.before(c,pc,w))reject(6);
}
'''+a)
    a='    if(status_reg<32u){'
    s=replace_exact(s,a,'''    if(restore.stage()){
        if(!v850::held(c)||ordinal||kind)reject(6);
        if(restore.stage()==3u){
            if(!restore.returned(c,pc)||restore.visits()!=16u||
               !v726::witness.restore_returned(c,pc,restore.visits(),true,12u)||
               !epilogue_guard.start(c,epilogue_labels,pc))reject(6);
            std::cout<<"V919_RESTORE_RETURN original_return=1 visits=16 gprs=15 follow_held=1"<<std::endl;
        }
        if(restore.stage()!=4u||!epilogue_guard.before(c,pc,w,0u,0u)||
           !v726::witness.before(c,pc,w,true))reject(6);
        if(w==0x4e800020u){
            if(v726::witness.stage()!=3u||epilogue_guard.visits()!=epilogue_labels.size()||
               epilogue_guard.writes())reject(6);
            std::cout<<"V919_HANDLER_EPILOGUE original_restore_return=1 gprs=15 abi=1 blr_boundary=1 handler_return=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        if(v726::witness.stage()!=2u)reject(6);
        return true;
    }
'''+a)
    a='    if(kind){'
    return replace_exact(s,a,'''    if(kind==1u&&ordinal==12u&&restore_enabled()){
        if(lane!=6u||index_branch.stage()!=5u||pc!=restore_expected.site||w!=restore_expected.branch||
           !v726::witness.before_authenticated(c,pc,w,true,12u)||
           !restore.start(c,pc,w,v726::witness.entry_gprs()))reject(6);
        std::cout<<std::dec<<"V868_HANDLER_SUFFIX_RESULT after="<<lane<<" next="<<ordinal<<" kind="<<kind
            <<" visits="<<guard.visits()<<" writes="<<guard.writes()<<" executed=0 handler_return=0 boot_verified=0"<<std::endl;
        std::cout<<"V919_RESTORE_START after=6 next=12 kind=1 original_call=1"<<std::endl;
        return true;
    }
'''+a)

def install(dol,elf,root,host):
    target,code,base,disp=plan(dol,elf)
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    sites=[pc for pc,x in call_census(HANDLER,words).items() if x==(12,1)]
    if len(sites)!=1:raise ValueError('restore edge')
    site=sites[0];branch=words[(site-HANDLER)//4]
    rows=epilogue(HANDLER,words,site)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('private tree')
    if audit_shared_alias((p.read_text() for p in paths),main.read_text(),target,code)!=16:
        raise ValueError('restore coverage')
    changes={};calls=entries=0
    for p in paths:
        s=p.read_text()
        if owns_root(s,HANDLER):
            body=exact_function(s,HANDLER);verify_direct(body,site,target)
            if audit_native([body],main.read_text(),{pc:(HANDLER,w) for pc,w in rows})!=len(rows):
                raise ValueError('epilogue coverage')
            for pc,w in rows:verify_handler_label(body,pc,w,0,0,False)
            calls+=1
        entries+=entry_count(s,target)
        if owns_root(s,target):
            body=exact_function(s,target)
            s=replace_exact(s,body,patch_alias(body,target,code))
            inc='#include "undercover/wii_handler_suffix_binding_v868.h"'
            if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
            changes[p]=s
    if len(changes)!=1 or calls!=1 or entries!=1:raise ValueError('restore coverage')
    dest=root/'nWiiRuntime/include/undercover'
    if dest.is_symlink():raise ValueError('destination')
    h=dest/'v919_private_handler_epilogue.h';g=dest/'wii_gpr_restore_v736.h'
    if h.exists() or h.is_symlink() or g.is_symlink():raise ValueError('destination')
    original=(host/g.name).read_text()
    if g.exists() and g.read_text()!=original:raise ValueError('restore witness identity')
    changes[g]=original
    changes[h]=('#pragma once\n#include "wii_gpr_restore_v736.h"\nnamespace undercover::wii::v868 {\n'
        +f'inline constexpr GprRestoreExpectation restore_expected{{0x{site:08x}u,0x{target:08x}u,0x{branch:08x}u,17u,{base}u,{disp}}};\n'
        +f'inline constexpr std::array<HandlerSuffixLabel,{len(rows)}> epilogue_labels{{{{'
        +','.join(f'HandlerSuffixLabel{{0x{pc:08x}u,0x{w:08x}u,0u,0u}}' for pc,w in rows)+'}};\n}\n')
    a=dest/'wii_si_ack_binding_v672.h';b=dest/'wii_handler_suffix_binding_v868.h'
    if any(p.is_symlink() or not p.is_file() for p in (a,b)):raise ValueError('destination')
    changes[a]=replace_exact(a.read_text(),'if(v868::active())v868::reject(6);','if(v868::active()){v868::observe(a,c);return;}')
    changes[b]=patch_binding(b.read_text())
    for p,s in changes.items():p.write_text(s)
    print('V919_HANDLER_EPILOGUE_ROUTE installed=1 restore_labels=16 epilogue_labels='+str(len(rows))+' execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError):
        print('V919_HANDLER_EPILOGUE_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
