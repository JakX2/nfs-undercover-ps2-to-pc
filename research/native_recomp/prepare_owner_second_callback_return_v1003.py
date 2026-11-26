#!/usr/bin/env python3
"""Join original second callback epilogue to the real interrupt handler."""
import argparse,struct,re
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_second_wireless_v1002 import plan as base_plan,header as base_header,install as base_install,patch_analyzer
from prepare_owner_callback_after_setter_v842 import plan as suffix_plan
from prepare_v667_si_dispatch import HANDLER,exact
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root
from prepare_owner_indirect_callback_v806 import verify_indirect
from verify_callback_resume_v853 import verify_callback_resume

def plan(dol,elf):
    result=list(base_plan(dol,elf));p=result[0];C=result[2];call=result[4];full=result[5]
    joined,c,resume,seen,stops=suffix_plan(dol,elf,True)
    original=joined[1][0][0]
    roots,edges,indirect,iw,hw,dw,guard,extra=p[0]
    if c!=C or len(seen)!=21:raise ValueError('suffix geometry')
    for i,w in enumerate(roots[C]):
        if w!=0x4e800020 and original[C][i]!=w:raise ValueError('suffix prefix')
    rsite,r=next((pc,dst) for pc,(i,k,dst) in stops.items() if i==13 and k==1)
    isite=next(pc for pc,(i,k,dst) in stops.items() if i==4 and k==2)
    restore=list(original[r]);tail=list(original[C][(rsite-C)//4+1:(rsite-C)//4+5])
    if len(restore)!=7 or len(tail)!=4:raise ValueError('restore geometry')
    if r in roots:
        if list(roots[r])!=restore:raise ValueError('restore overlap')
    else:
        for a,ws in roots.items():
            if a<r+4*len(restore) and r<a+4*len(ws):
                lo,hi=sorted((a,r));low=ws if lo==a else restore;high=restore if hi==r else ws
                if lo+4*len(low)!=hi+4*len(high) or list(low[(hi-lo)//4:])!=list(high):raise ValueError('restore overlap')
        roots[r]=restore
    roots[C]=list(original[C])
    if list(roots[C][(rsite-C)//4+1:(rsite-C)//4+5])!=tail:raise ValueError('restore geometry')
    extra=(*extra[:-1],(rsite,r,4*len(restore),full[(rsite-C)//4],restore),extra[-1])
    result[0]=((roots,edges,indirect,iw,hw,dw,guard,extra),*p[1:])
    return result,resume,seen,stops,rsite,r,restore,tail,isite,roots[HANDLER][(call+4-HANDLER)//4]

def header(result,resume,seen,stops,rsite,r,restore,tail,isite,caller_word,out):
    base_header(*result,out);C=result[2];call=result[4];roots=result[0][0][0]
    fmt=lambda xs:','.join(f'0x{x:08x}u' for x in xs)
    with out.open('a') as f:
        f.write('\n#include "wii_callback_suffix_v841.h"\n#include "wii_callback_return_v846.h"\n')
        f.write(f'inline constexpr uint32_t CallbackRestore=0x{r:08x}u,CallbackRestoreCall=0x{rsite:08x}u;\n')
        f.write('inline constexpr std::array<uint32_t,7> CallbackRestoreWords{'+fmt(restore)+'};\n')
        f.write('inline constexpr std::array<undercover::wii::CallbackSuffixWord,21> CallbackSuffixWords{{'+','.join('undercover::wii::CallbackSuffixWord{'+fmt((pc,roots[C][(pc-C)//4]))+'}' for pc in seen)+'}};\n')
        f.write('inline constexpr undercover::wii::CallbackSuffixExpectation CallbackSuffixExpected{'+fmt((C,C+688,resume))+',CallbackSuffixWords,{{'+','.join('undercover::wii::CallbackSuffixEdge{'+fmt((pc,dst or 0))+f',{i}u'+'}' for pc,(i,k,dst) in sorted(stops.items()))+'}}};\n')
        f.write('inline constexpr undercover::wii::CallbackReturnExpectation CallbackReturnExpected{'+fmt((rsite,r,call+4))+',CallbackRestoreWords,{'+fmt(tail)+'},'+fmt((caller_word,))+'};\n')

def install(result,resume,seen,stops,rsite,r,restore,tail,isite,caller_word,root):
    p=result[0];C=result[2];call=result[4]
    base_install(p,call,root)
    paths=sorted(root.glob('*.cpp'));main=root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')
    cp=[f for f in paths if owns_root(f.read_text(),C)]
    hp=[f for f in paths if owns_root(f.read_text(),HANDLER)]
    if len(cp)!=1 or len(hp)!=1:raise ValueError('resume owner')
    verify_indirect(exact_function(cp[0].read_text(),C),isite)
    text=hp[0].read_text();body=exact_function(text,HANDLER)
    verify_callback_resume(main.read_text(),body,HANDLER,call+4)
    pat=re.compile(r'(?mi)^loc_'+f'{call+4:X}'+r': ;\n    // 0x'+f'{call+4:08X}: {caller_word:08X}'+r'\n(?=    \+\+ctx\.inst_count;\n    rfi_test::before_owned)')
    if len(pat.findall(body))!=1:raise ValueError('resume label')
    out=pat.sub(lambda m:m[0]+f'    rfi_test::callback_resume(ctx,0x{call+4:08x}u,0x{caller_word:08x}u);\n',body,count=1)
    text=replace_exact(text,body,out)
    decl='namespace rfi_test {void before_owned(nwii::runtime::CPUContext&,uint32_t,uint32_t,uint32_t);}'
    hp[0].write_text(replace_exact(text,decl,decl+'\nnamespace rfi_test {void callback_resume(nwii::runtime::CPUContext&,uint32_t,uint32_t);}' ))
    print('V1003_CALLBACK_RESUME_ROUTE original_handler=1 original_restore=1 pre_tick_hook=1 execution=0')

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);a.add_argument('output',type=Path)
    m=a.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');x=a.parse_args()
    try:
        if x.dol.stat().st_size>MAX_DOL or x.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(x.dol.read_bytes(),x.elf.read_bytes())
        if x.install:install(*q,x.output)
        elif x.patch_analyzer:patch_analyzer(q[0][0],x.output)
        else:header(*q,x.output);print('V1003_CALLBACK_RETURN_GEOMETRY suffix_labels=21 restore_loads=6 original_caller=1 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration) as e:
        allowed=('suffix geometry','suffix prefix','restore geometry','restore overlap','resume owner','resume label','resume dispatcher identity','local resume dispatcher identity','native coverage','native owner','hook identity')
        print('V1003_CALLBACK_RETURN_PREP verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
