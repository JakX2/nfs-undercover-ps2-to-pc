#!/usr/bin/env python3
"""Restore the original second interrupt handler and resume its actual dispatcher."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import HANDLER,DISPATCH,exact
from prepare_owner_second_handler_frontier_v1004 import plan as base_plan,header as base_header,install as base_install,patch_analyzer
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
    extra=(*extra[:-1],(site,root,64,tail[0],tr),extra[-1])
    p[0]=(roots,edges,indirect,iw,hw,dw,guard,extra);result[0]=tuple(p)
    return q,site,root,tr,tail[1:],resume,word,added

def header(q,site,root,tr,tail,resume,word,added,out):
    base_header(*q,out)
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    with out.open('a') as f:
        f.write(f'\ninline constexpr uint32_t HandlerRestore=0x{root:08x}u,HandlerRestoreCall=0x{site:08x}u;\n')
        f.write(f'inline constexpr bool HandlerRestoreAdded={str(added).lower()};\n')
        f.write('inline constexpr std::array<uint32_t,16> HandlerRestoreWords{'+fmt(tr)+'};\n')
        f.write('inline constexpr undercover::wii::HandlerReturnExpectation HandlerReturnExpected{'+fmt((site,root,resume))+',HandlerRestoreWords,{'+fmt(tail)+'},'+fmt((word,))+'};\n')

def install(q,site,root,tr,tail,resume,word,added,tree):
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
        else:header(*q,x.output);print('V1006_HANDLER_RETURN_GEOMETRY restore_loads=15 tail_words=4 original_caller=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('handler tail geometry','handler tail words','handler restore overlap','handler suffix seam','dispatcher resume geometry','dispatcher owner','dispatcher resume coverage','dispatcher resume label','resume dispatcher identity','local resume dispatcher identity','native coverage','native owner','hook identity')
        print('V1006_HANDLER_RETURN_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
