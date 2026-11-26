#!/usr/bin/env python3
"""Independent concrete reference for the initialized diagnostic object's native leaf."""
import argparse,struct
from pathlib import Path
from private_plan_cache import memoized_plan
from prepare_post_stm_sc_report_dependency_abi import plan as abi_plan
from prepare_v419_full_start import MAX_DOL
from audit_handler_suffix_v728 import target

MASK=0xffffffff
def signed(v):return (v^0x80000000)-0x80000000
def rotate(v,n):return ((v<<n)|(v>>(32-n)))&MASK
def bitmask(mb,me):
    return sum(1<<(31-i) for i in range(32) if (mb<=i<=me if mb<=me else i>=mb or i<=me))
def execute(root,ws,args,obj,sites,initial):
    gp={3:args[0],4:args[1]};cr={};data=bytearray(initial)
    seen=set();accessed=set();pc=root;loads=stores=0
    def reg(r):
        if r not in gp:raise ValueError('dependency path undefined register')
        return gp[r]
    def put(r,v):
        if r not in (0,*range(3,13)):raise ValueError('dependency path nonvolatile')
        gp[r]=v&MASK
    def cmp(f,a,b):
        cr[f*4]=a<b;cr[f*4+1]=a>b;cr[f*4+2]=a==b
        # XER.SO is intentionally unknown; no branch may consume it.
        cr.pop(f*4+3,None)
    bypc={x[0]:x for x in sites}
    if len(bypc)!=len(sites) or len(data)!=obj[1]:raise ValueError('dependency path object')
    while True:
        if pc in seen or pc&3 or not root<=pc<root+4*len(ws):raise ValueError('dependency path control')
        seen.add(pc);w=ws[(pc-root)//4];op=w>>26;xo=(w>>1)&1023;rs=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31
        imm=((w&0xffff)^0x8000)-0x8000;next_pc=pc+4
        if w==0x4e800020:break
        if op in (10,11):
            if w&0x00200000:raise ValueError('dependency path compare')
            a,b=reg(ra),w&0xffff if op==10 else imm
            cmp((w>>23)&7,a if op==10 else signed(a),b)
        elif op in (14,15):put(rs,(reg(ra) if ra else 0)+(imm<<(16 if op==15 else 0)))
        elif op in (20,21,23):
            sh=reg(rb)&31 if op==23 else rb
            m=bitmask((w>>6)&31,(w>>1)&31);v=rotate(reg(rs),sh)&m
            put(ra,(reg(ra)&~m)|v if op==20 else v)
            if w&1:cmp(0,signed(reg(ra)),0)
        elif op in (24,25,26,27,28,29):
            n=(w&0xffff)<<(16 if op&1 else 0);a=reg(rs)
            put(ra,a|n if op<26 else a^n if op<28 else a&n)
            if op>=28:cmp(0,signed(reg(ra)),0)
        elif op==31 and xo in (444,28,316):
            a,b=reg(rs),reg(rb);put(ra,a|b if xo==444 else a&b if xo==28 else a^b)
            if w&1:cmp(0,signed(reg(ra)),0)
        elif op in (32,34,40,42,36,38,44):
            n={32:4,34:1,40:2,42:2,36:4,38:1,44:2}[op]
            wr=op in (36,38,44);addr=((reg(ra) if ra else 0)+imm)&MASK
            if bypc.get(pc)!=(pc,addr,n,wr) or pc in accessed or not obj[0]<=addr<addr+n<=obj[0]+obj[1]:
                raise ValueError('dependency path access')
            accessed.add(pc);off=addr-obj[0]
            if wr:
                data[off:off+n]=(reg(rs)&((1<<(8*n))-1)).to_bytes(n,'big');stores+=1
            else:
                put(rs,int.from_bytes(data[off:off+n],'big',signed=op==42));loads+=1
        elif op in (16,18):
            if w&3:raise ValueError('dependency path control')
            if op==18:next_pc=target(pc,w)
            else:
                bo=(w>>21)&31;bi=(w>>16)&31
                if not bo&4:raise ValueError('dependency path control')
                if bo&16:next_pc=target(pc,w)
                elif bi not in cr:raise ValueError('dependency path undefined CR')
                elif cr[bi]==bool(bo&8):next_pc=target(pc,w)
        else:raise ValueError('dependency path opcode')
        pc=next_pc
    return len(seen),loads,stores,reg(3),bytes(data)

@memoized_plan
def plan(d,e):
    _,args,obj,sites,kind,blob,fields,ws=abi_plan(d,e)
    result=execute(fields[0],ws,(args[0][1],args[1][1]),obj,sites,blob)
    if kind!=1:raise ValueError('dependency path initial kind')
    return result,blob

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','dependency path undefined register','dependency path nonvolatile','dependency path object','dependency path control','dependency path compare',
          'dependency path access','dependency path undefined CR','dependency path opcode','dependency path initial kind'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        (visits,loads,stores,value,data),initial=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_DEPENDENCY_PATH verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_DEPENDENCY_PATH verified=1 visits={visits} loads={loads} stores={stores} changed_bytes={sum(a!=b for a,b in zip(data,initial))} return_value_proven=1 initial_object=1 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
