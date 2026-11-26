#!/usr/bin/env python3
"""Private bounded dataflow census for original IOS_Ioctl request stores.

Symbolic values only, not a PPC interpreter. Unknown instructions discard
provenance instead of silently retaining stale register identities.
"""
import argparse,struct
from collections import Counter
from pathlib import Path
from prepare_v1385_async_ioctl_geometry import plan,IOCTL,EDGES
from prepare_v419_full_start import MAX_DOL,direct_bl

def C(n):return ('constant',n&0xffffffff)
def A(n):return ('argument',n)
def R(n=0):return ('request',n)
def S(n=0):return ('stack',n)
def P(n):return ('physical_argument',n)
def offset(x,n):
    if x is None:return None
    if n==0:return x
    if x[0]=='constant':return C(x[1]+n)
    if x[0] in ('request','stack','static'):return x[0],x[1]+n
    return None

def branch_target(pc,w):
    m,s=(0xfffc,0x8000) if w>>26==16 else (0x03fffffc,0x02000000)
    return (pc+((w&m)^s)-s)&0xffffffff

def mask32(mb,me):
    return sum(1<<(31-i) for i in range(32) if (mb<=i<=me if mb<=me else i>=mb or i<=me))
def rol32(x,n):return ((x<<n)|(x>>(32-n)))&0xffffffff

def logical(x,y,op):
    if x==y and op in ('or','and'):return x
    if x is not None and y is not None and x[0]==y[0]=='constant':
        return C({'or':lambda a,b:a|b,'and':lambda a,b:a&b,'xor':lambda a,b:a^b}[op](x[1],y[1]))
    if op=='or' and y==C(0):return x
    if op=='or' and x==C(0):return y
    if op=='and' and x is not None and x[0]=='argument' and y==C(0x3fffffff):return P(x[1])
    if op=='and' and y is not None and y[0]=='argument' and x==C(0x3fffffff):return P(y[1])
    return None

def apply(w,regs,stack,wire):
    op=w>>26;rt=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;xo=(w>>1)&1023
    d=((w&0xffff)^0x8000)-0x8000
    if op in (14,15):
        regs[rt]=offset(regs[ra] if ra else C(0),d<<(16 if op==15 else 0))
    elif op in (24,25,26,27,28,29):
        regs[ra]=logical(regs[rt],C((w&0xffff)<<(16 if op in (25,27,29) else 0)),
                         'or' if op in (24,25) else 'xor' if op in (26,27) else 'and')
    elif op==21:
        x=regs[rt];sh=rb;mb=(w>>6)&31;me=(w>>1)&31;mask=mask32(mb,me)
        if x is not None and x[0]=='constant':regs[ra]=C(rol32(x[1],sh)&mask)
        elif sh==0 and mask==0xffffffff:regs[ra]=x
        elif sh==0 and mask==0x3fffffff and x is not None and x[0]=='argument':regs[ra]=P(x[1])
        else:regs[ra]=None
    elif op in (20,23):regs[ra]=None
    elif op in (36,37):
        ea=offset(regs[ra] if ra else C(0),d)
        if ea is None:raise ValueError('request unknown store base')
        if ea[0]=='request':
            if ea[1]&3 or not 0<=ea[1]<=60:raise ValueError('request store range')
            wire[ea[1]]=regs[rt]
        if ea is not None and ea[0]=='stack':stack[ea[1]]=regs[rt]
        if op==37:regs[ra]=ea
    elif op==32:
        ea=offset(regs[ra] if ra else C(0),d)
        regs[rt]=(stack.get(ea[1]) if ea is not None and ea[0]=='stack' else
                  wire.get(ea[1]) if ea is not None and ea[0]=='request' else None)
    elif op in (33,34,35,40,41,42,43):
        regs[rt]=None
        if op&1:regs[ra]=None
    elif op in (38,39,44,45,47,52,53,54,55,60,61):
        # Do not silently skip a store into the candidate request.
        if regs[ra] is None or regs[ra][0]=='request':raise ValueError('request unmodeled store')
        if op in (39,45,53,55,61):regs[ra]=None
    elif op in (10,11,16,18,19):pass
    elif op==31:
        if xo in (444,28,316):
            regs[ra]=logical(regs[rt],regs[rb],{444:'or',28:'and',316:'xor'}[xo])
        elif xo==266:
            a,b=regs[ra],regs[rb]
            regs[rt]=offset(a,b[1]) if b is not None and b[0]=='constant' else offset(b,a[1]) if a is not None and a[0]=='constant' else None
        elif xo in (0,32,144,467,598,854):pass
        elif xo in (19,339,83,23,87,279,343,40,104,235,459,491):regs[rt]=None
        elif xo in (26,24,536,792,824,954,922,476,124):regs[ra]=None
        else:raise ValueError('request unmodeled instruction')
    elif op in (7,8,12,13):regs[rt]=None
    else:raise ValueError('request unmodeled instruction')

def paths(root,words,edges):
    if not words or len(words)>256 or len(edges)!=6:raise ValueError('request geometry')
    calls=dict(edges);save,alloc,flush1,flush2,submit,restore=(pc for pc,_ in edges)
    regs=[None]*32;regs[1]=S();regs[2]=('static',2);regs[13]=('static',13)
    for i in range(3,11):regs[i]=A(i)
    pending=[(root,regs,{}, {},(),(),frozenset())];finished=[];nodes=0;unallocated=0
    end=root+4*len(words)
    while pending:
        pc,regs,stack,wire,flushes,history,visited=pending.pop()
        nodes+=1
        if nodes>4096 or len(finished)>64 or pc in visited or pc&3 or not root<=pc<end:
            raise ValueError('request path budget')
        visited=visited|{pc};w=words[(pc-root)//4];op=w>>26
        if pc==submit:
            if direct_bl(w,pc)!=calls[pc]:raise ValueError('request submit edge')
            # This audit covers only the allocated lane already required
            # by the native fixture. Count, do not claim infeasible, any
            # syntactic paths bypassing that independently verified call.
            if alloc not in history:unallocated+=1;continue
            finished.append((regs[3],dict(wire),flushes));continue
        if pc==restore or w==0x4e800020:continue
        if op==18 and w&1:
            if calls.get(pc)!=direct_bl(w,pc) or pc not in (save,alloc,flush1,flush2):raise ValueError('request call')
            if pc in (flush1,flush2):flushes=flushes+((pc,regs[3],regs[4]),)
            if pc!=save:
                for i in (0,*range(3,13)):regs[i]=None
            if pc==alloc:regs[3]=R();wire={}
            history=history+(pc,)
            pending.append((pc+4,regs,stack,wire,flushes,history,visited));continue
        if op in (16,18):
            if w&3:raise ValueError('request branch')
            dst=branch_target(pc,w)
            pending.append((dst,regs.copy(),dict(stack),dict(wire),flushes,history,visited))
            if op==16 and (w>>21)&20!=20:pending.append((pc+4,regs,stack,wire,flushes,history,visited))
            continue
        apply(w,regs,stack,wire)
        pending.append((pc+4,regs,stack,wire,flushes,history,visited))
    if not finished:raise ValueError('request no submit path')
    return finished,nodes,unallocated

def verify(paths_result):
    rows,nodes,unallocated=paths_result
    expected={0:{C(6)},8:{A(3)},12:{A(4)},16:{P(5),C(0)},20:{A(6)},24:{P(7),C(0)},28:{A(8)}}
    layouts=set();flush_counts=set()
    for req,wire,flushes in rows:
        if req!=R() or any(wire.get(off) not in allowed for off,allowed in expected.items()):
            raise ValueError('request wire provenance')
        callback=[off for off,val in wire.items() if val==A(9)]
        userdata=[off for off,val in wire.items() if val==A(10)]
        if len(callback)!=1 or len(userdata)!=1 or min(callback+userdata)<32 or callback==userdata:
            raise ValueError('request callback provenance')
        layouts.add((callback[0],userdata[0]));flush_counts.add(len(flushes))
        if not 0<len(flushes)<=2:raise ValueError('request flush coverage')
    if len(layouts)!=1:raise ValueError('request callback layout')
    return next(iter(layouts)),len(rows),nodes,min(flush_counts),max(flush_counts),unallocated

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        roots,*_=plan(q.dol.read_bytes(),q.elf.read_bytes())
        _,count,nodes,lo,hi,unallocated=verify(paths(IOCTL,roots[IOCTL],EDGES))
        print(f'V1390_REQUEST_DATAFLOW verified=1 allocated_submit_paths={count} unallocated_static_paths={unallocated} states={nodes} wire_fields=7 callback_fields=2 flush_min={lo} flush_max={hi} original_execution=0')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed={'size','request geometry','request store range','request unknown store base','request unmodeled store','request unmodeled instruction','request path budget',
            'request submit edge','request call','request branch','request no submit path','request wire provenance',
            'request callback provenance','request flush coverage','request callback layout'}
        print('V1390_REQUEST_DATAFLOW verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
