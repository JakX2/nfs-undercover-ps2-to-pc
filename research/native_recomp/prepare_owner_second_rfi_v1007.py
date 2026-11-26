#!/usr/bin/env python3
"""Restore the original second interrupt handler and resume its actual dispatcher."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import HANDLER,DISPATCH,exact
from prepare_owner_second_handler_frontier_v1004 import plan as base_plan,header as base_header,install as base_install,patch_analyzer
from prepare_owner_scheduler_v722 import plan as sched_plan,E,S,H,target
from prepare_owner_context_v720 import plan as loader_plan,L
from prepare_owner_irq_join_v923 import dispatcher_shape
from prepare_v667_si_dispatch import DISABLE,RESTORE
from prepare_owner_handler_tail_v879 import plan as tail_plan
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root
from verify_callback_resume_v853 import verify_callback_resume

def plan(dol,elf):
    q=list(base_plan(dol,elf));result=q[0];p=list(result[0])
    roots,edges,indirect,iw,hw,dw,guard,extra=p[0]
    ((tail_roots,site,root,_,_,_),frame,off)=tail_plan(dol,elf)
    original=exact(dol,elf,HANDLER,len(roots[HANDLER]))
    tail=original[(site-HANDLER)//4:(site-HANDLER)//4+5]
    tr=tail_roots[root]
    if len(tail)!=5 or len(tr)!=16 or site not in guard or roots[HANDLER][(site-HANDLER)//4]!=0x4e800020:raise ValueError('handler tail geometry')
    if list(roots[HANDLER][(site-HANDLER)//4+1:(site-HANDLER)//4+5])!=list(tail[1:]):raise ValueError('handler tail words')
    added=root not in roots
    if not added and list(roots[root])!=list(tr):raise ValueError('handler restore overlap')
    for a,ws in roots.items():
        if a==root or a>=root+4*len(tr) or root>=a+4*len(ws):continue
        lo,hi=sorted((a,root));low=ws if lo==a else tr;high=tr if hi==root else ws
        if lo+4*len(low)!=hi+4*len(high) or list(low[(hi-lo)//4:])!=list(high):raise ValueError('handler restore overlap')
    roots[root]=list(tr)
    roots[HANDLER][(site-HANDLER)//4]=tail[0];guard.remove(site)
    rows=p[10]
    if site in rows:
        if rows[site]!=(0x4e800020,12,1):raise ValueError('handler suffix seam')
        rows[site]=(tail[0],12,1)
    old=f'HandlerSuffixLabel{{0x{site:08x}u,0x4e800020u,12u,1u}}'
    new=f'HandlerSuffixLabel{{0x{site:08x}u,0x{tail[0]:08x}u,12u,1u}}'
    q[-1]=replace_exact(q[-1],old,new)
    resume=indirect+4;dispatch=exact(dol,elf,DISPATCH,len(roots[DISPATCH]));word=dispatch[(resume-DISPATCH)//4]
    if resume not in guard or roots[DISPATCH][(resume-DISPATCH)//4]!=0x4e800020 or word==0x4e800020:raise ValueError('dispatcher resume geometry')
    roots[DISPATCH][(resume-DISPATCH)//4]=word
    code=list(exact(dol,elf,resume,4));reg=dispatcher_shape(resume,code)
    sr,counter,hint,D,R,G,calls=sched_plan(dol,elf);loader,gqr=loader_plan(dol,elf)
    if (D,R)!=(DISABLE,RESTORE) or any(list(sr[a])!=list(roots[a]) for a in (D,R)):raise ValueError('epilogue shared')
    added_roots={E:sr[E],S:sr[S],L:loader,G:sr[G],H:[0x60000000,0x4e800020]}
    for a,ws in added_roots.items():
        if any(a<b+4*len(v) and b<a+4*len(ws) for b,v in roots.items()):raise ValueError('epilogue overlap')
        roots[a]=list(ws)
    for i,w in enumerate(code):
        pc=resume+4*i
        if pc not in guard or roots[DISPATCH][(pc-DISPATCH)//4]!=(code[0] if i==0 else 0x4e800020):raise ValueError('epilogue seam')
        roots[DISPATCH][(pc-DISPATCH)//4]=w
    switch=[S+4*i for i,w in enumerate(sr[S]) if w>>26==18 and not(w&1) and target(S+4*i,w)==G]
    if len(switch)!=1:raise ValueError('epilogue switch')
    guard.update((switch[0],L+4*(len(loader)-1),G))
    new=[]
    for pc,dst in [(resume,E),(resume+4,S),(resume+12,L),*calls]:
        owner=DISPATCH if resume<=pc<resume+16 else E
        w=roots[owner][(pc-owner)//4]
        new.append((pc,dst,4*len(roots[dst]),w,roots[dst]))
    extra=(*extra[:-1],(site,root,64,tail[0],tr),*new,extra[-1])
    p[0]=(roots,edges,indirect,iw,hw,dw,guard,extra);result[0]=tuple(p)
    return q,site,root,tr,tail[1:],resume,word,added,added_roots,code,reg,counter,hint,G,gqr

def header(q,site,root,tr,tail,resume,word,added,added_roots,code,reg,counter,hint,G,gqr,out):
    base_header(*q,out)
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    with out.open('a') as f:
        f.write(f'\ninline constexpr uint32_t HandlerRestore=0x{root:08x}u,HandlerRestoreCall=0x{site:08x}u;\n')
        f.write(f'inline constexpr bool HandlerRestoreAdded={str(added).lower()};\n')
        f.write('inline constexpr std::array<uint32_t,16> HandlerRestoreWords{'+fmt(tr)+'};\n')
        f.write('inline constexpr undercover::wii::HandlerReturnExpectation HandlerReturnExpected{'+fmt((site,root,resume))+',HandlerRestoreWords,{'+fmt(tail)+'},'+fmt((word,))+'};\n')

        f.write('\n#include "wii_live_epilogue_v762.h"\n')
        for i,(a,ws) in enumerate(added_roots.items()):
            f.write(f'inline constexpr std::array<uint32_t,{len(ws)}> epilogue_code_{i}{{'+fmt(ws)+'};\n')
        f.write(f'inline constexpr std::array<undercover::wii::WirelessCode,{len(added_roots)}> EpilogueRoots{{{{'+','.join(f'undercover::wii::WirelessCode{{0x{a:08x}u,epilogue_code_{i}}}' for i,a in enumerate(added_roots))+'}};\n')
        f.write('inline constexpr undercover::wii::LiveEpilogueExpectation SecondEpilogueExpected{'+fmt((resume,E,S,DISABLE,RESTORE,L,G,0x806f5318))+f',{counter},{hint},{reg}u,{gqr}u'+'};\n')
        f.write(f'inline constexpr uint32_t SecondResume=0x{H:08x}u;\n')

def install(q,site,root,tr,tail,resume,word,added,added_roots,code,reg,counter,hint,G,gqr,tree):
    base_install(*q,tree)
    paths=sorted(tree.glob('*.cpp'));main=tree/('main_output.cpp' if (tree/'main_output.cpp').is_file() else 'output.cpp')
    found=[p for p in paths if owns_root(p.read_text(),DISPATCH)]
    if len(found)!=1:raise ValueError('dispatcher owner')
    path=found[0];s=path.read_text();body=exact_function(s,DISPATCH);outer=main.read_text()
    verify_callback_resume(outer,body,DISPATCH,resume)
    if audit_native([body],outer.split('extern "C" void run_game(',1)[1],{resume:(DISPATCH,word)})!=1:raise ValueError('dispatcher resume coverage')
    pat=re.compile(r'(?mi)^loc_'+f'{resume:X}'+r': ;\n    // 0x'+f'{resume:08X}: {word:08X}'+r'\n    \+\+ctx\.inst_count;\n')
    if len(pat.findall(body))!=1:raise ValueError('dispatcher resume label')
    out=pat.sub(lambda m:m[0].replace('    ++ctx.inst_count;\n',f'    rfi_test::handler_resume(ctx,0x{resume:08x}u,0x{word:08x}u);\n    ++ctx.inst_count;\n    rfi_test::before_owned(ctx,0x{DISPATCH:08x}u,0x{resume:08x}u,0x{word:08x}u);\n'),body,count=1)
    expected={resume+4*i:(DISPATCH,w) for i,w in enumerate(code)}
    if audit_native([body],outer.split('extern "C" void run_game(',1)[1],expected)!=4:raise ValueError('epilogue coverage')
    for pc,(_,w) in sorted(expected.items()):
        if pc==resume:continue
        pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        if len(pat.findall(out))!=1:raise ValueError('epilogue hook')
        out=pat.sub(lambda m:m[0]+f'    rfi_test::before_owned(ctx,0x{DISPATCH:08x}u,0x{pc:08x}u,0x{w:08x}u);\n',out,count=1)
    s=replace_exact(s,body,out)
    decl='namespace rfi_test {void before_owned(nwii::runtime::CPUContext&,uint32_t,uint32_t,uint32_t);}'
    path.write_text(replace_exact(s,decl,decl+'\nnamespace rfi_test {void handler_resume(nwii::runtime::CPUContext&,uint32_t,uint32_t);}' ))
    print('V1006_HANDLER_RESUME_ROUTE original_dispatcher=1 original_restore=1 pre_tick_hook=1 execution=0')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(*q,x.output)
        elif x.patch_analyzer:patch_analyzer(q[0][0][0],x.output)
        else:header(*q,x.output);print('V1007_EPILOGUE_GEOMETRY dispatcher_words=4 loader_words=54 scheduler_enable=1 reschedule=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('handler tail geometry','handler tail words','handler restore overlap','handler suffix seam','dispatcher resume geometry','dispatcher owner','dispatcher resume coverage','dispatcher resume label','resume dispatcher identity','local resume dispatcher identity','native coverage','native owner','hook identity')
        print('V1007_EPILOGUE_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
