#!/usr/bin/env python3
"""Private reference for actual helper continuation following the first dependency."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan
from prepare_post_stm_sc_report_helper_prefix import prefix
from prepare_post_stm_sc_report_dependency_abi import arguments,compose,plan as dependency_abi
from prepare_post_stm_sc_report_dependency_path import plan as leaf_path,signed
from prepare_post_stm_sc_report_abi import model as report_model
from prepare_post_stm_sc_report import REPORT
from prepare_post_stm_sc_version import plan as version_plan
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_handler_suffix_v728 import target
from prepare_post_stm_sc_report_helper import census

def resume(root,words,start,registers,result):
    edges,reach,returns,_,_,_,_,_=census(root,words)
    gp=list(registers)
    for r in (0,*range(3,13)):gp[r]=('unknown',r)
    gp[3]=('const',result)
    cr={};seen=set();pc=start
    def add(v,n):
        if not n:return v
        if v[0] in ('const','stack'):return (v[0],(v[1]+n)&0xffffffff if v[0]=='const' else v[1]+n)
        raise ValueError('helper resume unknown arithmetic')
    while True:
        if pc not in reach or pc in seen:raise ValueError('helper resume path')
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        imm=((w&0xffff)^0x8000)-0x8000;seen.add(pc);nxt=pc+4
        if pc in edges:return tuple(gp),tuple(sorted(seen)),pc,edges[pc],1
        if w==0x4e800020:return tuple(gp),tuple(sorted(seen)),pc,0,0
        # The first stack load admits a separate original epilogue witness.
        if op==32 and ra==1:return tuple(gp),tuple(sorted(seen)),pc,0,2
        if op in (10,11):
            a=gp[ra];b=w&0xffff if op==10 else imm
            if a[0]!='const' or w&0x00200000:raise ValueError('helper resume compare')
            v=a[1] if op==10 else signed(a[1]);f=(w>>23)&7
            cr[f*4]=v<b;cr[f*4+1]=v>b;cr[f*4+2]=v==b
        elif op in (14,15) and rs!=1:
            gp[rs]=add(gp[ra] if ra else ('const',0),imm<<(16 if op==15 else 0))
        elif op in (24,25) and ra!=1:
            v=gp[rs];n=(w&0xffff)<<(16 if op==25 else 0)
            if v[0]!='const' and n:raise ValueError('helper resume unknown arithmetic')
            gp[ra]=('const',v[1]|n) if v[0]=='const' else v
        elif op==31 and xo==444 and rs==rb and not w&1 and ra!=1:gp[ra]=gp[rs]
        elif op==16 and not w&3:
            bo=(w>>21)&31;bi=(w>>16)&31
            if not bo&4:raise ValueError('helper resume branch')
            if bo&16:nxt=target(pc,w)
            elif bi not in cr:raise ValueError('helper resume compare')
            elif cr[bi]==bool(bo&8):nxt=target(pc,w)
        elif op==18 and not w&3:nxt=target(pc,w)
        else:raise ValueError('helper resume opcode')
        pc=nxt

def formatter_args(args,object_pointer,format_pointer,va):
    if len(args)!=4 or args[0][0]!='const' or args[0][1]&3 or not 0x80004000<=args[0][1]<0x81800000:
        raise ValueError('helper resume callback')
    if args[1]!=('const',object_pointer) or args[2]!=('const',format_pointer) or args[3]!=va or va[0]!='stack':
        raise ValueError('helper resume argument identity')
    return args[0][1]

def plan(d,e,*,details=False):
    prior=helper_plan(d,e);root,_,leaf,_,frame=prior[3]
    sizes=parse_functions(e);ws=exact_words(d,e,root,30)
    report=exact_words(d,e,REPORT,sizes[REPORT]//4)
    report_regs,_=report_model(REPORT,report,details=True)
    _,_,_,fields=version_plan(d,e)
    initial={2:EXPECTED_GPRS[2],13:EXPECTED_GPRS[13],3:fields[5],4:fields[4]}
    report_regs=tuple(('const',initial[v[1]]) if v[0]=='reg' and v[1] in initial else v for v in report_regs)
    helper_regs,_,_,_=prefix(root,ws,details=True)
    gp=tuple(compose(v,report_regs,128) for v in helper_regs)
    (visits,loads,stores,result,data),_=leaf_path(d,e)
    final,path,site,dst,kind=resume(root,ws,root+52,gp,result)
    if kind==1:
        if sizes.get(dst)!=535*4:raise ValueError('helper resume formatter')
        exact_words(d,e,dst,1)
    args=final[3:7]
    if kind!=1:raise ValueError('helper resume formatter')
    _,leaf_args,*_=dependency_abi(d,e)
    callback=formatter_args(args,leaf_args[0][1],fields[5],report_regs[4])
    size=sizes.get(callback,0)
    if not 4<=size<=65536 or size%4:raise ValueError('helper resume callback')
    exact_words(d,e,callback,1)
    if details:return root,ws,path,site,dst,args,exact_words(d,e,dst,1)[0],callback,exact_words(d,e,callback,1)[0]
    return len(path),kind,args,size//4

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','helper resume unknown arithmetic','helper resume path','helper resume compare','helper resume branch','helper resume opcode','helper resume formatter','helper resume callback','helper resume argument identity'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        visits,kind,args,callback_words=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_HELPER_RESUME verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_HELPER_RESUME verified=1 labels={visits} boundary_kind={kind} formatter_called={int(kind==1)} leaf_return_proven=1 callback_words={callback_words} object_identity=1 format_identity=1 va_identity=1 original_execution=0')
    print('POST_STM_SC_REPORT_HELPER_RESUME_ARGS '+' '.join(f'arg{i+1}={v[0]}' for i,v in enumerate(args)))
    return 0
if __name__=='__main__':raise SystemExit(main())
