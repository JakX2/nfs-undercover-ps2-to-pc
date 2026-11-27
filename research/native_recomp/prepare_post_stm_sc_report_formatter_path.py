#!/usr/bin/env python3
"""Private symbolic first formatter path with exact initialized input provenance."""
import argparse,struct
from pathlib import Path
from private_plan_cache import memoized_plan
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
def first_path(root,ws,args,stack_slots,readonly,caller_sp=-160,*,start=None,resume=None,details=False,
               seed_bytes=None,initial_cr=None,initial_ctr=None,entry_lr=('lr',0),read_resolver=None,read_refusal=None,control_refusal=None,local_ctr_edge=None,stack_refusal=None,partial_origin=None,step_observer=None,partial_caller_stores=()):
    if (start is None)!=(resume is None):raise ValueError('formatter resume state')
    seen,bounds,_=closure(root,ws,start)
    edge_used=False
    if local_ctr_edge is not None:
        site,dst=local_ctr_edge
        if resume is not None or not root<=site<root+4*len(ws) or not root<dst<root+4*len(ws) or (site|dst)&3 or site==dst or ws[(site-root)//4]!=0x4e800420:
            raise ValueError('formatter local CTR geometry')
    gp=[('reg',r) for r in range(32)];gp[1]=('stack',caller_sp)
    for r,v in args.items():gp[r]=v
    mem=dict(seed_bytes or {});cr=dict(initial_cr or {});ctr=initial_ctr;lr=entry_lr
    path=[];accesses=[];frame=0;saves=set();protected=set()
    if seed_bytes is not None and (stack_slots or resume is not None or any(not caller_sp<=at<8 for at in mem)):
        raise ValueError('formatter nested memory geometry')
    if resume is not None and (initial_cr is not None or initial_ctr is not None or (entry_lr!=('lr',0) and partial_origin is None)):
        raise ValueError('formatter nested state')
    if resume is not None:
        rg,rm,rc,ctr,lr,frame,rs=resume
        gp=list(rg);mem=dict(rm);cr=dict(rc);saves=set(rs)
        if args or stack_slots or len(gp)!=32 or not 8<=frame<=4096 or frame%8 or gp[1]!=('stack',caller_sp-frame):
            raise ValueError('formatter resume state')
        protected.update(range(caller_sp-frame,caller_sp-frame+4))
        protected.update(range(caller_sp+4,caller_sp+8))
        for at,v in mem.items():
            if v[0]=='part' and v[1][0]=='reg' and 14<=v[1][1]<=31:protected.add(at)
    # Optional symbolic-only continuation. Missing bytes are opaque identities,
    # never integer values. Restrict new identities to the one admitted word.
    if partial_origin is not None:
        if resume is None or not isinstance(partial_origin,tuple) or len(partial_origin)!=2:
            raise ValueError('formatter partial origin')
        origin,width=partial_origin
        if width!=4 or origin%4 or not caller_sp-frame+4<=origin<=caller_sp-4 or any(origin+i in protected for i in range(4)):
            raise ValueError('formatter partial origin')
        if not 0<sum(origin+i not in mem for i in range(4))<4:
            raise ValueError('formatter partial origin')
    # Explicit, owner-local symbolic exception for a bounded caller buffer.
    # No existing parent cell, frame linkage, or saved register can be replaced.
    caller_store_used=set()
    if partial_caller_stores:
        if partial_origin is None or len(partial_caller_stores)>8:raise ValueError('formatter partial caller contract')
        occupied=set()
        pcs=set()
        for site,at,n,kind in partial_caller_stores:
            if site&3 or not root<=site<root+4*len(ws) or site in pcs or n not in (1,2,4) or at%n or not caller_sp+8<=at<at+n<=8 or kind not in ('const','partial'):
                raise ValueError('formatter partial caller contract')
            if any(i in occupied or i in mem or i in protected for i in range(at,at+n)):
                raise ValueError('formatter partial caller contract')
            occupied.update(range(at,at+n));pcs.add(site)
    def bytes_of(v,n):
        if v[0]=='partial':
            if partial_origin is None or n not in (1,2,4):raise ValueError('formatter partial store')
            return v[1][-n:]
        if v[0]=='const':return tuple(('byte',(v[1]>>(8*(n-1-i)))&255) for i in range(n))
        return tuple(('part',v,n,i) for i in range(n))
    for at,v in stack_slots.items():
        for i,x in enumerate(bytes_of(v,4)):mem[at+i]=x
    def stack_read(at,n):
        cells=tuple(mem.get(at+i) for i in range(n))
        if all(x is not None and x[0]=='byte' for x in cells):
            return const(int.from_bytes(bytes(x[1] for x in cells),'big'))
        if all(x is not None and x[0]=='part' and x[1]==cells[0][1] and x[2:]==(n,i) for i,x in enumerate(cells)):
            return cells[0][1]
        caller_copy=any(site in caller_store_used and start<=at<at+n<=start+width for site,start,width,_ in partial_caller_stores)
        if partial_origin is not None and n in (1,2,4) and not at%n and (caller_sp-frame+4<=at<at+n<=caller_sp or caller_copy):
            origin,width=partial_origin
            if all(x is not None or origin<=at+i<origin+width for i,x in enumerate(cells)):
                parts=tuple(('uninitialized',at+i) if x is None else x for i,x in enumerate(cells))
                if any(x[0]=='uninitialized' for x in parts):
                    return ('partial',(('byte',0),)*(4-n)+parts)
        raise ValueError('formatter stack read provenance')
    def read(a,n):
        k,at=a
        if k=='stack':
            try:return stack_read(at,n)
            except ValueError:
                if stack_refusal is not None:
                    stack_refusal(at,n,tuple(path),frame,tuple(accesses),tuple(gp),dict(mem),dict(cr),ctr,lr,frozenset(saves))
                raise
        if k!='const':raise ValueError('formatter pointer provenance')
        matches=[blob[at-base:at-base+n] for base,blob in readonly if base<=at<at+n<=base+len(blob)]
        if len(matches)==1:return const(int.from_bytes(matches[0],'big'))
        if matches or read_resolver is None or any(at<base+len(blob) and base<at+n for base,blob in readonly):
            raise ValueError('formatter data read provenance')
        try:
            value=read_resolver(at,n)
            if not isinstance(value,bytes) or len(value)!=n:raise ValueError('formatter data read provenance')
        except ValueError:
            if read_refusal is not None:
                read_refusal(at,n,tuple(path),frame,tuple(accesses),tuple(gp),dict(mem),dict(cr),ctr,lr,frozenset(saves))
            raise
        return const(int.from_bytes(value,'big'))
    def write(a,v,n=4):
        k,at=a
        if k=='stack' and partial_caller_stores and at>=caller_sp+8:
            admitted=(pc,at,n,v[0])
            if admitted not in partial_caller_stores or pc in caller_store_used or any(i in mem or i in protected for i in range(at,at+n)):
                raise ValueError('formatter partial caller write')
            caller_store_used.add(pc)
            for i,x in enumerate(bytes_of(v,n)):mem[at+i]=x
            return
        if k!='stack' or not frame or n not in (1,2,4) or at%n or not caller_sp-frame<=at<at+n<=caller_sp+8:
            raise ValueError('formatter stack write provenance')
        if at>=caller_sp and (at!=caller_sp+4 or n!=4 or v!=entry_lr):
            raise ValueError('formatter caller linkage provenance')
        if resume is None and any(at+i in mem for i in range(n)):
            raise ValueError('formatter duplicate stack write')
        if resume is not None and any(at+i in protected for i in range(n)):
            raise ValueError('formatter protected stack write')
        for i,x in enumerate(bytes_of(v,n)):mem[at+i]=x
        if n==4 and v[0]=='reg' and 14<=v[1]<=31:saves.add(v[1])
    def cmp(f,a,b):
        cr[f*4]=a<b;cr[f*4+1]=a>b;cr[f*4+2]=a==b
        cr.pop(f*4+3,None)
    def record(v):cmp(0,signed(val(v)),0)
    pc=root if start is None else start
    while True:
        if pc not in seen or len(path)>=512:raise ValueError('formatter path bound')
        path.append(pc);w=ws[(pc-root)//4];op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        imm=((w&0xffff)^0x8000)-0x8000;nxt=pc+4
        if step_observer is not None:step_observer(pc,w,tuple(gp),dict(mem))
        if pc in bounds:
            if local_ctr_edge is not None and pc==local_ctr_edge[0]:
                dst=local_ctr_edge[1]
                if edge_used or w!=0x4e800420 or ctr!=dst or dst in path or not frame:
                    raise ValueError('formatter local CTR identity')
                extra_seen,extra_bounds,_=closure(root,ws,dst)
                seen|=extra_seen;bounds|=extra_bounds;edge_used=True;pc=dst;continue
            if w>>26==18 and w&3==1 or (resume is not None and w==0x4e800421 and ctr is not None):
                if not frame or stack_read(caller_sp-frame,4)!=('stack',caller_sp) or stack_read(caller_sp+4,4)!=entry_lr:
                    raise ValueError('formatter frame identity')
                if local_ctr_edge is not None and not edge_used:raise ValueError('formatter local CTR unused')
                dst=direct_bl(w,pc) if w>>26==18 else ctr
                result=(path,frame,accesses,len(saves),dst,tuple(gp),dict(mem))
                state=(tuple(gp),dict(mem),dict(cr),ctr,lr,frame,frozenset(saves))
                return result+(state,) if details else result
            if control_refusal is not None:
                control_refusal(pc,w,tuple(path),frame,tuple(accesses),tuple(gp),dict(mem),dict(cr),ctr,lr,frozenset(saves))
            raise ValueError('formatter other boundary')
        if op==37 and rs==ra==1:
            if frame or not -4096<=imm<=-8 or imm%8:raise ValueError('formatter frame identity')
            frame=-imm;write(add(gp[1],imm),gp[1]);gp[1]=add(gp[1],imm);accesses.append((pc,'stack_write',4,caller_sp-frame))
        elif op in (36,37,38,39,44,45,47):
            n={36:4,37:4,38:1,39:1,44:2,45:2,47:4}[op]
            addr=add(gp[ra] if ra else const(0),imm)
            count=32-rs if op==47 else 1
            for j in range(count):write(add(addr,n*j),gp[rs+j],n)
            accesses.append((pc,'stack_write',n*count,addr[1]))
            if op in (37,39,45):
                if not ra or ra==1:raise ValueError('formatter update store')
                gp[ra]=addr
        elif op==31 and xo in (151,183,215,247,407,439):
            n={151:4,183:4,215:1,247:1,407:2,439:2}[xo]
            a,b=gp[ra] if ra else const(0),gp[rb]
            if b[0]=='const':addr=add(a,signed(b[1]))
            elif a[0]=='const':addr=add(b,signed(a[1]))
            else:raise ValueError('formatter indexed store provenance')
            write(addr,gp[rs],n);accesses.append((pc,'stack_write',n,addr[1]))
            if xo in (183,247,439):
                if not ra or ra==1:raise ValueError('formatter update store')
                gp[ra]=addr
        elif op in (32,33,34,35,40,41,42,43):
            n={32:4,33:4,34:1,35:1,40:2,41:2,42:2,43:2}[op]
            a=add(gp[ra] if ra else const(0),imm)
            v=read(a,n)
            if op in (42,43):v=const((val(v)^0x8000)-0x8000)
            gp[rs]=v;accesses.append((pc,a[0]+'_read',n,a[1]))
            if op&1:
                if not ra or ra==rs:raise ValueError('formatter update load')
                gp[ra]=a
        elif op==31 and xo in (23,55,87,119,279,311,343,375):
            n={23:4,55:4,87:1,119:1,279:2,311:2,343:2,375:2}[xo]
            update=xo in (55,119,311,375)
            if w&1 or rs==1 or (update and (not ra or ra==rs or ra==1)):
                raise ValueError('formatter indexed load form')
            a,b=gp[ra] if ra else const(0),gp[rb]
            if b[0]=='const':addr=add(a,signed(b[1]))
            elif a[0]=='const':addr=add(b,signed(a[1]))
            else:raise ValueError('formatter indexed load provenance')
            if addr[0] not in ('stack','const') or addr[1]%n:
                raise ValueError('formatter indexed load provenance')
            v=read(addr,n)
            if xo in (343,375):v=const((val(v)^0x8000)-0x8000)
            gp[rs]=v;accesses.append((pc,addr[0]+'_read',n,addr[1]))
            if update:gp[ra]=addr
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

@memoized_plan
def plan(d,e,*,details=False):
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
    result=first_path(root,ws,initial,slots,readonly,details=details)
    path,frame,accesses,saved,dst,gp,mem=result[:7]
    if sizes.get(dst)!=48:raise ValueError('formatter first dependency')
    exact_words(d,e,dst,1)
    return (*result[:7],ws,result[7],readonly) if details else (*result,ws)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','formatter unknown arithmetic','formatter unknown value','formatter stack read provenance','formatter pointer provenance','formatter data read provenance','formatter stack write provenance','formatter caller linkage provenance','formatter duplicate stack write','formatter update store','formatter indexed store provenance','formatter path bound','formatter frame identity','formatter other boundary','formatter update load','formatter compare','formatter branch','formatter CTR provenance','formatter CR provenance','formatter first dependency'}
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
    print(f'POST_STM_SC_REPORT_FORMATTER_PATH verified=1 visits={len(path)} unique={len(set(path))} frame_bytes={frame} stack_store_sites={sum(k=="stack_write" for _,k,_,_ in accesses)} loads={sum(k.endswith("_read") for _,k,_,_ in accesses)} nonvolatile_saves={saved} first_dependency=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
