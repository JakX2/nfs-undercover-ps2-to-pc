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
from collect_third_alarm_suffix_v1044 import collect_after_alarm
from audit_handler_third_v740 import edge as handler_edge
from audit_v662_external_overlay import expected as installed_vector
from prepare_v663_external_entry import TRAMP
from make_private_elf_symbol_map import parse_functions
from prepare_v709_os_leaves import entry_count

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
    alarm_site,_,_=handler_edge(HANDLER,original,5)
    after=collect_after_alarm(HANDLER,original,roots[HANDLER],guard,alarm_site+4)
    return q,site,root,tr,tail[1:],resume,word,added,added_roots,code,reg,counter,hint,G,gqr,after

def header(q,site,root,tr,tail,resume,word,added,added_roots,code,reg,counter,hint,G,gqr,after,out):
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
        f.write(f'inline constexpr std::array<undercover::wii::HandlerSuffixLabel,{len(after)}> AfterThirdAlarm{{{{'+','.join('undercover::wii::HandlerSuffixLabel{'+fmt((pc,w))+f',{o}u,{k}u'+'}' for pc,(w,o,k) in sorted(after.items()))+'}};\n')

def install(q,site,root,tr,tail,resume,word,added,added_roots,code,reg,counter,hint,G,gqr,after,tree):
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
    print(f'V1032_ALARM_SUFFIX_GEOMETRY labels={len(after)} original_call=6 execution=0')

def vector_plan(dol,elf,q):
    roots=q[0][0][0][0][0]
    if parse_functions(elf).get(TRAMP)!=80:raise ValueError('third trampoline extent')
    words=list(exact(dol,elf,TRAMP,20))
    if words[-1]>>26!=18 or words[-1]&3 or target(TRAMP+76,words[-1])!=DISPATCH:
        raise ValueError('third trampoline tail')
    added={0x80000500:list(installed_vector(dol)),TRAMP:words}
    if len(added[0x80000500])!=38 or any(a<b+4*len(v) and b<a+4*len(ws) for a,ws in added.items() for b,v in roots.items()):
        raise ValueError('third vector ownership')
    return added

def vector_header(q,added,out):
    header(*q,out)
    fmt=lambda ws:','.join(f'0x{w:08x}u' for w in ws)
    with out.open('a') as f:
        f.write('\n#include "wii_second_vector_v939.h"\n')
        f.write(f'inline constexpr uint32_t ThirdVectorRoot=0x80000500u,ThirdTrampolineRoot=0x{TRAMP:08x}u;\n')
        for name,ws in zip(('ThirdVectorWords','ThirdTrampolineWords'),added.values()):
            f.write(f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+fmt(ws)+'};\n')
        f.write('inline constexpr undercover::wii::SecondVectorExpectation ThirdVectorExpected{ThirdTrampolineRoot,Dispatcher,0x806f5318u,dispatcher_words[0],ThirdVectorWords,ThirdTrampolineWords};\n')

def vector_analyzer(q,added,root):
    # Extend analyzer ownership without making the legacy bounded call
    # traversal follow the vector's cross-root exception return.
    p=q[0][0][0]
    old=p[0]
    joined={**old[0],**added}
    patch_analyzer(((joined,*old[1:]),*p[1:]),root)

def vector_install(q,added,tree):
    install(*q,tree)
    paths=sorted(tree.glob('*.cpp'));main=tree/('main_output.cpp' if (tree/'main_output.cpp').is_file() else 'output.cpp')
    outer=main.read_text().split('extern "C" void run_game(',1)[1]
    changes={}
    for a,ws in added.items():
        found=[p for p in paths if owns_root(p.read_text(),a)]
        entries=sum(entry_count(p.read_text(),a) for p in paths)
        if len(found)!=1 or entries!=1:
            print(f'V1071_VECTOR_OWNER_REFUSAL lane={1 if a==0x80000500 else 2} owners={len(found)} entries={entries}')
            raise ValueError('third vector owner')
        path=found[0];s=changes.get(path,path.read_text());body=exact_function(s,a);out=body
        expected={a+4*i:(a,w) for i,w in enumerate(ws)}
        if audit_native([body],outer,expected)!=len(ws):raise ValueError('third vector coverage')
        for pc,(_,w) in expected.items():
            pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
            if len(pat.findall(out))!=1:raise ValueError('third vector hook')
            out=pat.sub(lambda m:m[0]+f'    rfi_test::before_owned(ctx,0x{a:08x}u,0x{pc:08x}u,0x{w:08x}u);\n',out,count=1)
        s=replace_exact(s,body,out)
        decl='namespace rfi_test {void before_owned(nwii::runtime::CPUContext&,uint32_t,uint32_t,uint32_t);}'
        if decl not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+decl)
        changes[path]=s
    for path,s in changes.items():path.write_text(s)
    print('V1069_THIRD_VECTOR_ROUTE installed=1 vector_labels=38 trampoline_labels=20 original_dispatcher=1 execution=0')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(x.dol.read_bytes(),x.elf.read_bytes())
        added=vector_plan(x.dol.read_bytes(),x.elf.read_bytes(),q)
        if x.install:vector_install(q,added,x.output)
        elif x.patch_analyzer:vector_analyzer(q,added,x.output)
        else:vector_header(q,added,x.output);print('V1007_EPILOGUE_GEOMETRY dispatcher_words=4 loader_words=54 scheduler_enable=1 reschedule=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('handler tail geometry','handler tail words','handler restore overlap','handler suffix seam','dispatcher resume geometry','dispatcher owner','dispatcher resume coverage','dispatcher resume label','resume dispatcher identity','local resume dispatcher identity','native coverage','native owner','hook identity','third alarm suffix extent','third alarm suffix call','third alarm suffix boundary','third alarm suffix word','third alarm suffix geometry','third alarm suffix guard','third trampoline extent','third trampoline tail','third vector ownership','third vector owner','third vector coverage','third vector hook')
        print('V1007_EPILOGUE_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
