#!/usr/bin/env python3
"""Private reference for the formatter's first small conditional-return leaf."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_formatter_path import plan as formatter_plan,const,add,val
from prepare_post_stm_sc_report_dependency_path import signed,rotate,bitmask
from prepare_post_stm_sc_report_dependency_abi import plan as leaf_abi
from prepare_post_stm_sc_report_dependency_path import execute as dependency_execute
from prepare_post_stm_sc_version import plan as version_plan
from prepare_v419_full_start import MAX_DOL
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_handler_suffix_v728 import target
from audit_osinit_suffix_v929 import category
MASK=0xffffffff

def cfg(root,ws):
    seen=set();work=[root];returns=set();back=0
    while work:
        pc=work.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<root+4*len(ws):raise ValueError('formatter leaf escape')
        seen.add(pc);w=ws[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op==19 and xo==16 and not w&1:
            bo=(w>>21)&31
            if not bo&4:raise ValueError('formatter leaf CTR return')
            returns.add(pc)
            if not bo&16:work.append(pc+4)
        elif op in (16,18) and not w&3:
            dst=target(pc,w);back+=int(dst<=pc);work.append(dst)
            if op==16:
                bo=(w>>21)&31
                if not bo&4:raise ValueError('formatter leaf CTR branch')
                if not bo&16:work.append(pc+4)
        elif category(w) in ('load','integer'):work.append(pc+4)
        else:raise ValueError('formatter leaf unsupported control')
    if not returns:raise ValueError('formatter leaf return')
    return seen,returns,back

def run(root,ws,initial,readonly,stack):
    reach,returns,back=cfg(root,ws)
    gp=list(initial);cr={};path=[];reads=[];pc=root
    def write(r,v):
        if r not in (0,*range(3,13)):raise ValueError('formatter leaf nonvolatile')
        gp[r]=v
    def read(a,n):
        kind,at=a
        if kind=='stack':
            cells=tuple(stack.get(at+i) for i in range(n))
            if all(x is not None and x[0]=='byte' for x in cells):
                return const(int.from_bytes(bytes(x[1] for x in cells),'big'))
            if all(x is not None and x[0]=='part' and x[1]==cells[0][1] and x[2:]==(n,i) for i,x in enumerate(cells)):
                return cells[0][1]
            raise ValueError('formatter leaf stack read')
        if kind!='const':raise ValueError('formatter leaf pointer')
        matches=[blob[at-base:at-base+n] for base,blob in readonly if base<=at<at+n<=base+len(blob)]
        if len(matches)!=1:raise ValueError('formatter leaf data read')
        return const(int.from_bytes(matches[0],'big'))
    def cmp(f,a,b):
        cr[f*4]=a<b;cr[f*4+1]=a>b;cr[f*4+2]=a==b;cr.pop(f*4+3,None)
    def taken(w):
        bo=(w>>21)&31;bi=(w>>16)&31
        if not bo&4:raise ValueError('formatter leaf CTR branch')
        if bo&16:return True
        if bi not in cr:raise ValueError('formatter leaf CR provenance')
        return cr[bi]==bool(bo&8)
    while True:
        if pc not in reach or len(path)>=512:raise ValueError('formatter leaf bound')
        path.append(pc);w=ws[(pc-root)//4];op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        imm=((w&0xffff)^0x8000)-0x8000;nxt=pc+4
        if op==19 and xo==16 and not w&1:
            if taken(w):
                if pc not in returns:raise ValueError('formatter leaf return')
                return path,reads,gp[3],reach,returns
        elif op in (16,18):
            if w&3:raise ValueError('formatter leaf unsupported control')
            if op==18 or taken(w):nxt=target(pc,w)
        elif op in (14,15):write(rs,add(gp[ra] if ra else const(0),imm<<(16 if op==15 else 0)))
        elif op in (10,11):
            if w&0x00200000:raise ValueError('formatter leaf compare')
            a=val(gp[ra]);b=w&0xffff if op==10 else imm;cmp((w>>23)&7,a if op==10 else signed(a),b)
        elif op==31 and xo in (0,32):
            if w&0x00200000:raise ValueError('formatter leaf compare')
            a,b=val(gp[ra]),val(gp[rb]);cmp((w>>23)&7,a if xo==32 else signed(a),b if xo==32 else signed(b))
        elif op in (32,33,34,35,40,41,42,43):
            n={32:4,33:4,34:1,35:1,40:2,41:2,42:2,43:2}[op]
            a=add(gp[ra] if ra else const(0),imm);v=read(a,n)
            if op in (42,43):v=const((val(v)^0x8000)-0x8000)
            write(rs,v);reads.append((pc,a,n))
            if op&1:
                if not ra or ra==rs:raise ValueError('formatter leaf update')
                write(ra,a)
        elif op==31 and xo==444 and rs==rb:
            write(ra,gp[rs])
            if w&1:cmp(0,signed(val(gp[ra])),0)
        elif op==31 and xo in (922,954):
            bits=16 if xo==922 else 8;m=(1<<bits)-1;s=1<<(bits-1)
            write(ra,const(((val(gp[rs])&m)^s)-s))
            if w&1:cmp(0,signed(val(gp[ra])),0)
        elif op in (20,21,23):
            sh=val(gp[rb])&31 if op==23 else rb;m=bitmask((w>>6)&31,(w>>1)&31);v=rotate(val(gp[rs]),sh)&m
            write(ra,const((val(gp[ra])&~m)|v if op==20 else v))
            if w&1:cmp(0,signed(val(gp[ra])),0)
        else:raise ValueError(f'formatter leaf opcode {category(w)} {len(path)}')
        pc=nxt

def plan(d,e):
    path,frame,accesses,saved,root,gp,mem,ws=formatter_plan(d,e)
    if parse_functions(e).get(root)!=48:raise ValueError('formatter leaf extent')
    body=exact_words(d,e,root,12)
    _,_,ranges,_=version_plan(d,e)
    _,args,obj,sites,_,blob,fields,leaf=leaf_abi(d,e)
    result=dependency_execute(fields[0],leaf,(args[0][1],args[1][1]),obj,sites,blob)
    readonly=tuple(ranges)+((obj[0],result[4]),)
    return run(root,body,gp,readonly,mem)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','formatter leaf escape','formatter leaf CTR return','formatter leaf CTR branch','formatter leaf unsupported control','formatter leaf return','formatter leaf nonvolatile','formatter leaf stack read','formatter leaf pointer','formatter leaf data read','formatter leaf CR provenance','formatter leaf bound','formatter leaf compare','formatter leaf update','formatter leaf extent','formatter unknown value','formatter unknown arithmetic'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        path,reads,value,reach,returns=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter leaf opcode '):
            _,_,_,kind,n=reason.split()
            if kind in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'POST_STM_SC_FORMATTER_LEAF_PATH verified=0 reason=opcode category={kind} ordinal={n}');return 1
        print('POST_STM_SC_FORMATTER_LEAF_PATH verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_FORMATTER_LEAF_PATH verified=1 visits={len(path)} unique={len(set(path))} static_reachable={len(reach)} return_sites={len(returns)} reads={len(reads)} return_kind={value[0]} writes=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
