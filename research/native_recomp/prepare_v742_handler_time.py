#!/usr/bin/env python3
"""Use the exact already-instrumented __OSGetSystemTime root a second time."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from audit_handler_third_v740 import edge,summarize
from si_nested_geometry_v693 import nested_plan
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root
def plan(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    site,target,branch=edge(HANDLER,words,3)
    _,root,size,_,code=nested_plan(dol,elf)
    if target!=root:raise ValueError('distinct time root')
    s,_=summarize(root,code)
    if s['words']!=25 or s['direct']!=3 or any(s[k] for k in ('conditional','backward','indirect','tail','mtmsr','system')) or s['returns']!=1 or code[-1]!=0x4e800020:
        raise ValueError('time shape')
    return site,root,root+size,branch
def render(row):
    return '#pragma once\n#include "wii_si_first_helper_v680.h"\nnamespace undercover::wii::v742 {inline constexpr SiHelperExpectation expected{'+','.join(f'0x{x:08x}u' for x in row)+'};}\n'
def patch_nested(s):
    a='#include "wii_si_os_leaf_binding_v709.h"'
    s=replace_exact(s,a,a+'\n#include "wii_si_handler_time_binding_v742.h"')
    a='    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Idle)return;'
    return replace_exact(s,a,a+'\n    if(v742::route.active()){v742::before(c,pc,word,ordinal,kind);return;}')
def patch_leaf(s):
    a='#include "wii_si_completion_ack_v668.h"'
    s=replace_exact(s,a,a+'\n#include "wii_si_handler_time_binding_v742.h"')
    a='    if(!active)return;\n    if(cursor>=3||ordinal!=cursor+1'
    return replace_exact(s,a,'    if(v742::route.active()){v742::leaf_before(c,pc,word,ordinal);return;}\n'+a)
def patch_ack(s):
    a='    if(v709::active)return v709::poll(c);'
    s=replace_exact(s,a,'    if(v742::route.active())return v742::poll(c);\n'+a)
    a='if(v680::observe(a,c)||v688::observe(a,c))return;'
    return replace_exact(s,a,'if(v742::observe(a,c))return;'+a)
def patch_handler(s):
    a='#include "wii_si_handler_return_v725.h"'
    s=replace_exact(s,a,a+'\n#include "wii_si_handler_time_binding_v742.h"')
    a='    if(!witness.before(c,pc,w,held())){'
    b=r'''    if(v742::route.active()){
        v742::returned(c,pc);
        if(!witness.helper_returned(c,pc,v742::route.total(),held(),3))reject(3);
        std::cout<<"V742_TIME_RESULT returned=1 abi=1 leaves=3 visits="<<v742::route.visits()<<" total="<<v742::route.total()<<" handler_return=0 boot_verified=0"<<std::endl;
        if(!v742::continue_suffix())std::_Exit(0);
    }
    const bool allow=v742::eligible(pc,w,ordinal,kind);
    if(!(allow?witness.before_authenticated(c,pc,w,held(),3):witness.before(c,pc,w,held()))){'''
    s=replace_exact(s,a,b)
    a='        reject(3);\n    }\n'
    # A newly encountered linked call is a verified refusal, never an executed dependency.
    s=replace_exact(s,a,r'''        if(v742::continue_suffix()&&v742::route.stage()==4&&witness.failure()==4&&
           ordinal>=4&&ordinal<=12&&kind>=1&&kind<=2){
            std::cout<<"V747_NEXT_BOUNDARY ordinal="<<ordinal<<" kind="<<kind<<" visits="<<witness.visits()<<" polls="<<witness.polls()<<" executed=0"<<std::endl;
        }
        reject(3);
    }
''')
    a='    if(witness.stage()==3)std::cout<<"V726_HANDLER_STAGE n=3"<<std::endl;'
    return replace_exact(s,a,'    if(allow){v742::start(c,pc,w);return;}\n'+a)
def install(dol,elf,root,host):
    row=plan(dol,elf);site,target,_,_=row
    paths=sorted(root.glob('output_*.cpp'))
    if len(paths)<20 or any(p.is_symlink() or p.stat().st_size>64*1024*1024 for p in paths):raise ValueError('private tree')
    owners=[exact_function(s,HANDLER) for p in paths if owns_root(s:=p.read_text(),HANDLER)]
    if len(owners)!=1:raise ValueError('handler owner')
    verify_direct(owners[0],site,target)
    dest=root/'nWiiRuntime/include/undercover'
    new={dest/n:(host/n).read_text() for n in ('wii_si_handler_time_v742.h','wii_si_handler_time_binding_v742.h')}
    new[dest/'v742_private_time_expectations.h']=render(row)
    edits={dest/n:fn for n,fn in (
        ('wii_si_nested_binding_v693.h',patch_nested),('wii_si_os_leaf_binding_v709.h',patch_leaf),
        ('wii_si_ack_binding_v672.h',patch_ack),('wii_si_handler_return_binding_v726.h',patch_handler))}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in new) or any(p.is_symlink() for p in edits):raise ValueError('destination')
    for p,fn in edits.items():new[p]=fn(p.read_text())
    for p,s in new.items():p.write_text(s)
    print('V742_TIME_ROUTE installed=1 same_nested_root=1 direct_edges=1 reused_leaf_roots=3 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('distinct time root','time shape','private tree','handler owner','destination','helper call label','helper direct native call','helper native return edge')
        print('V742_TIME_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
