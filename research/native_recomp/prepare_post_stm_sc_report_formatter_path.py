#!/usr/bin/env python3
"""Private symbolic first formatter path with exact initialized input provenance."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_resume import plan as resume_plan
from prepare_post_stm_sc_report_formatter import closure
from prepare_post_stm_sc_report_abi import model as report_model
from prepare_post_stm_sc_report import REPORT
from prepare_post_stm_sc_report_dependency_abi import plan as leaf_abi
from prepare_post_stm_sc_report_dependency_path import execute,signed,rotate,bitmask
from prepare_post_stm_sc_version import plan as version_plan
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from prepare_stm_final_return import spr
from audit_handler_suffix_v728 import target
from audit_osinit_suffix_v929 import category
MASK=0xffffffff
def const(v):return ('const',v&MASK)
def add(a,n):
    if a[0]=='const':return const(a[1]+n)
    if a[0]=='stack':return ('stack',a[1]+n)
    if not n:return a
    raise ValueError('formatter unknown arithmetic')
def val(v):
    if v[0]!='const':raise ValueError('formatter unknown value')
    return v[1]
def first_path(root,ws,args,stack_slots,readonly,caller_sp=-160):
    seen,bounds,_=closure(root,ws)
    gp=[('reg',r) for r in range(32)];gp[1]=('stack',caller_sp)
    for r,v in args.items():gp[r]=v
    mem=dict(stack_slots);cr={};ctr=None;lr=('lr',0);path=[];accesses=[];frame=0;saves=set()
    def read(a,n):
        k,at=a
        if k=='stack':
            if n==4 and at in mem:return mem[at]
            for base,v in mem.items():
                if base<=at and at+n<=base+4 and v[0]=='const':
                    return const((v[1]>>(8*(base+4-at-n)))&((1<<(8*n))-1))
            raise ValueError('formatter stack read provenance')
        if k!='const':raise ValueError('formatter pointer provenance')
        matches=[blob[at-base:at-base+n] for base,blob in readonly if base<=at<at+n<=base+len(blob)]
        if len(matches)!=1:raise ValueError('formatter data read provenance')
        return const(int.from_bytes(matches[0],'big'))
    def write(a,v):
        k,at=a
        if k!='stack' or not frame or not caller_sp-frame<=at<=caller_sp+4 or at&3 or at in mem:
            raise ValueError('formatter stack write provenance')
        mem[at]=v
        if v[0]=='reg' and 14<=v[1]<=31:saves.add(v[1])
    def cmp(f,a,b):
        cr[f*4]=a<b;cr[f*4+1]=a>b;cr[f*4+2]=a==b
        cr.pop(f*4+3,None)
    def record(v):cmp(0,signed(val(v)),0)
    pc=root
    while True:
        if pc not in seen or len(path)>=512:raise ValueError('formatter path bound')
        path.append(pc);w=ws[(pc-root)//4];op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        imm=((w&0xffff)^0x8000)-0x8000;nxt=pc+4
        if pc in bounds:
            if w>>26==18 and w&3==1:
                if not frame or mem.get(caller_sp-frame)!=('stack',caller_sp) or mem.get(caller_sp+4)!=('lr',0):
                    raise ValueError('formatter frame identity')
                return path,frame,accesses,len(saves),direct_bl(w,pc),tuple(gp),dict(mem)
            raise ValueError('formatter other boundary')
        if op==37 and rs==ra==1:
            if frame or not -4096<=imm<=-8 or imm%8:raise ValueError('formatter frame identity')
            frame=-imm;write(add(gp[1],imm),gp[1]);gp[1]=add(gp[1],imm);accesses.append((pc,'stack_write',4))
        elif op in (36,47) and ra==1:
            for j in range(32-rs if op==47 else 1):
                write(add(gp[1],imm+4*j),gp[rs+j])
            accesses.append((pc,'stack_write',4*(32-rs if op==47 else 1)))
        elif op in (32,33,34,35,40,41,42,43):
            n={32:4,33:4,34:1,35:1,40:2,41:2,42:2,43:2}[op]
            a=add(gp[ra] if ra else const(0),imm)
            v=read(a,n)
            if op in (42,43):v=const((val(v)^0x8000)-0x8000)
            gp[rs]=v;accesses.append((pc,a[0]+'_read',n))
            if op&1:
                if not ra or ra==rs:raise ValueError('formatter update load')
                gp[ra]=a
        elif op==31 and xo==339 and spr(w)==8:gp[rs]=lr
        elif op==31 and xo==467 and spr(w)==9:ctr=val(gp[rs])
        elif op in (14,15):gp[rs]=add(gp[ra] if ra else const(0),imm<<(16 if op==15 else 0))
        elif op in (10,11):
            if w&0x00200000:raise ValueError('formatter compare')
            a=val(gp[ra]);b=w&0xffff if op==10 else imm;cmp((w>>23)&7,a if op==10 else signed(a),b)
        elif op==31 and xo in (0,32):
            if w&0x00200000:raise ValueError('formatter compare')
            a,b=val(gp[ra]),val(gp[rb]);cmp((w>>23)&7,a if xo==32 else signed(a),b if xo==32 else signed(b))
        elif op==31 and xo==444 and rs==rb:gp[ra]=gp[rs]
        elif op==31 and xo in (922,954):
            bits=16 if xo==922 else 8;m=(1<<bits)-1;s=1<<(bits-1)
            gp[ra]=const(((val(gp[rs])&m)^s)-s)
        elif op in (20,21,23):
            sh=val(gp[rb])&31 if op==23 else rb;m=bitmask((w>>6)&31,(w>>1)&31)
            v=rotate(val(gp[rs]),sh)&m
            gp[ra]=const((val(gp[ra])&~m)|v if op==20 else v)
        elif op in (24,25,26,27,28,29):
            n=(w&0xffff)<<(16 if op&1 else 0)
            a=val(gp[rs]);gp[ra]=const(a|n if op<26 else a^n if op<28 else a&n)
            if op>=28:record(gp[ra])
        elif op==31 and xo in (266,40):
            a,b=gp[ra],gp[rb]
            if xo==266 and b[0]=='const':gp[rs]=add(a,signed(b[1]))
            elif xo==266 and a[0]=='const':gp[rs]=add(b,signed(a[1]))
            elif xo==40 and a[0]==b[0] and a[0] in ('stack','const'):gp[rs]=const(b[1]-a[1])
            else:raise ValueError('formatter unknown arithmetic')
        elif op in (16,18):
            if w&3:raise ValueError('formatter branch')
            if op==18:nxt=target(pc,w)
            else:
                bo=(w>>21)&31;bi=(w>>16)&31
                ct=True
                if not bo&4:
                    if ctr is None:raise ValueError('formatter CTR provenance')
                    ctr=(ctr-1)&MASK;ct=bool(ctr)!=bool(bo&2)
                if not bo&16 and bi not in cr:raise ValueError('formatter CR provenance')
                if ct and (bo&16 or cr[bi]==bool(bo&8)):nxt=target(pc,w)
        else:
            raise ValueError(f'formatter opcode {category(w)} {len(path)}')
        if op in (20,21,23) and w&1:record(gp[ra])
        if op==31 and xo in (444,922,954,266,40) and w&1:record(gp[rs if xo in (266,40) else ra])
        pc=nxt

def plan(d,e):
    _,_,_,_,root,args,_,_,_=resume_plan(d,e,details=True)
    sizes=parse_functions(e);ws=exact_words(d,e,root,535)
    _,_,ranges,fields=version_plan(d,e)
    _,slots=report_model(REPORT,exact_words(d,e,REPORT,sizes[REPORT]//4),details=True)
    regs={2:const(EXPECTED_GPRS[2]),13:const(EXPECTED_GPRS[13]),3:const(fields[5]),4:const(fields[4])}
    slots={at:regs.get(v[1],v) if v[0]=='reg' else v for at,v in slots.items()}
    _,la,obj,sites,_,blob,lf,lw=leaf_abi(d,e)
    result=execute(lf[0],lw,(la[0][1],la[1][1]),obj,sites,blob)
    readonly=tuple(ranges)+((obj[0],result[4]),)
    initial={i+3:v for i,v in enumerate(args)};initial.update({r:regs[r] for r in (2,13)})
    path,frame,accesses,saved,dst,gp,mem=first_path(root,ws,initial,slots,readonly)
    if sizes.get(dst)!=48:raise ValueError('formatter first dependency')
    exact_words(d,e,dst,1)
    return path,frame,accesses,saved,dst,gp,mem,ws

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','formatter unknown arithmetic','formatter unknown value','formatter stack read provenance','formatter pointer provenance','formatter data read provenance','formatter stack write provenance','formatter path bound','formatter frame identity','formatter other boundary','formatter update load','formatter compare','formatter branch','formatter CTR provenance','formatter CR provenance','formatter first dependency'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        path,frame,accesses,saved,dst,gp,mem,ws=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter opcode '):
            _,_,kind,n=reason.split()
            if kind in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'POST_STM_SC_REPORT_FORMATTER_PATH verified=0 reason=opcode category={kind} ordinal={n}');return 1
        print('POST_STM_SC_REPORT_FORMATTER_PATH verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_FORMATTER_PATH verified=1 visits={len(path)} unique={len(set(path))} frame_bytes={frame} stack_store_sites={sum(k=="stack_write" for _,k,_ in accesses)} loads={sum(k.endswith("_read") for _,k,_ in accesses)} nonvolatile_saves={saved} first_dependency=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
