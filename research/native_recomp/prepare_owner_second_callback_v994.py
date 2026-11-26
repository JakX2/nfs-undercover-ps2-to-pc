#!/usr/bin/env python3
"""Connect the genuine second handler's indirect callback to its native prologue."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import HANDLER,exact
from prepare_owner_second_shared_v988 import plan as base_plan,header as base_header
from prepare_owner_second_alarm_v985 import install as base_install,patch_analyzer
from prepare_owner_callback_prefix_v797 import plan as prefix_plan
from prepare_owner_indirect_callback_v806 import verify_indirect
from prepare_v789_alarm_suffix import expectations
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root

def plan(dol,elf):
    p,shared=base_plan(dol,elf)
    roots,edges,indirect,iw,hw,dw,guard,extra=p[0]
    pr,C,S,site,_,_=prefix_plan(dol,elf)
    candidate,full,sites=expectations(dol,elf)
    call=sites[0]
    raw=exact(dol,elf,HANDLER,len(roots[HANDLER]))
    if candidate!=C or call not in guard or raw[(call-HANDLER)//4]!=0x4e800421 or C in roots:
        raise ValueError('callback geometry')
    if list(pr[C][:-1])!=list(full[:len(pr[C])-1]):raise ValueError('callback prefix')
    roots[HANDLER][(call-HANDLER)//4]=0x4e800421
    guard.remove(call)
    roots[C]=list(pr[C])
    for a,ws in roots.items():
        if a==C:continue
        if a<C+4*len(pr[C]) and C<a+4*len(ws):raise ValueError('callback overlap')
    if S not in roots or list(roots[S])!=list(pr[S]):raise ValueError('callback save alias')
    # This direct edge is audited, but the callback prologue witness, not
    # the ordinary ACK call stack, owns its separate indirect dispatch.
    extra=(*extra,(site,S,4*len(pr[S]),pr[C][(site-C)//4],pr[S]))
    q=(roots,edges,indirect,iw,hw,dw,guard,extra)
    # Preserve shared-time edge as last for the existing header renderer.
    q=(*q[:-1],(*extra[:-2],extra[-1],extra[-2]))
    tail=list(p[1:]);tail[8]=[r for r in tail[8] if r[0]!=call]
    return (q,*tail),shared,C,S,call,full,sites

def header(p,shared,C,S,call,full,sites,out):
    base_header(p,shared,out);s=out.read_text()
    roots=p[0][0];fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    s+='#include "wii_callback_prefix_v800.h"\n#include "wii_callback_identity_v796.h"\n'
    s+=f'inline constexpr uint32_t CallbackRoot=0x{C:08x}u,CallbackSave=0x{S:08x}u,CallbackCall=0x{call:08x}u;\n'
    for name,ws in (('callback_code',roots[C]),('callback_prefix',roots[C][:-1]),('callback_save',roots[S]),('callback_full',full),('callback_sites',sites)):
        s+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+fmt(ws)+'};\n'
    out.write_text(s)

def install(p,call,root):
    owners=[exact_function(f.read_text(),HANDLER) for f in root.glob('*.cpp') if owns_root(f.read_text(),HANDLER)]
    if len(owners)!=1:raise ValueError('callback owner')
    verify_indirect(owners[0],call)
    base_install(p,root)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        p,shared,C,S,call,full,sites=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(p,call,x.output)
        elif x.patch_analyzer:patch_analyzer(p,x.output)
        else:header(p,shared,C,S,call,full,sites,x.output);print('V994_CALLBACK_GEOMETRY original_indirect=1 original_prefix=1 shared_save=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('callback geometry','callback prefix','callback overlap','callback save alias','callback owner','indirect label','indirect LR','indirect dispatch','indirect fallback','native coverage','native owner','hook identity')
        print('V994_CALLBACK_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
