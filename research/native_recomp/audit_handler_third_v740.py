#!/usr/bin/env python3
"""Bounded original dependency census, never emit original instructions or addresses."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER,shape
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE,TIME,SCHED
from make_private_elf_symbol_map import parse_functions,HEADER,SECTION,SYMBOL
from audit_si_deep_v695 import census,call_kind
from audit_handler_suffix_v728 import target
from si_second_geometry_v688 import second_plan
from si_nested_geometry_v693 import nested_plan
# Only SDK names known independently of the game. Never print raw symbol strings.
KNOWN=('SITransfer','__SITransfer','SIGetType','SIGetTypeAsync','SIGetStatus','SISetXY','SISetSamplingRate',
       'SIGetResponse','SIGetResponseRaw','SIEnablePolling','SIDisablePolling','SITransferCommands',
       'SIInterruptHandler','CompleteTransfer','GetTypeCallback','__OSGetSystemTime','OSGetTime',
       'OSDisableInterrupts','OSRestoreInterrupts','OSSetAlarm','OSCancelAlarm','OSSetPeriodicAlarm',
       'OSGetTick','__OSSetAlarm','OSGetCurrentThread','OSGetCurrentContext','OSDisableScheduler','OSEnableScheduler',
       '__OSReschedule','__OSGetTime','SIIsBusy','SIIsChanBusy','SIGetTypeAsync','SISetCommand',
       '__SIGetType','SIGetTypeCallback','SIGetTypeAsyncCallback','SIGetTypeCallback','SIGetResponseRaw')
def names(elf,address,allowlist=KNOWN):
    h=HEADER.unpack_from(elf);off,unit,n=h[6],h[11],h[12]
    if unit!=SECTION.size or not 1<=n<10000 or off+n*unit>len(elf):raise ValueError('section table')
    rows=[SECTION.unpack_from(elf,off+i*unit) for i in range(n)]
    out=set()
    for _,kind,_,_,at,size,link,_,_,entsize in rows:
        if kind!=2:continue
        if entsize!=SYMBOL.size or size%entsize or at+size>len(elf) or not 0<=link<n:raise ValueError('symbol table')
        st=rows[link]
        if st[1]!=3 or st[4]+st[5]>len(elf):raise ValueError('string table')
        for pos in range(at,at+size,entsize):
            name,addr,_,info,_,shndx=SYMBOL.unpack_from(elf,pos)
            if addr!=address or info&15 not in (0,2) or not 0<shndx<n or name>=st[5]:continue
            lo=st[4]+name;hi=elf.find(b'\0',lo,min(lo+256,st[4]+st[5]))
            if hi<0:continue
            raw=elf[lo:hi]
            for k in allowlist:
                if raw==k.encode():out.add(k)
    return ','.join(sorted(out)) or 'unclassified'
def edge(root,words,ordinal):
    _,direct,indirect=shape(root,words)
    rows=sorted([*direct,*[(pc,None) for pc in indirect]])
    if not 1<=ordinal<=len(rows):raise ValueError('call census')
    pc,dst=rows[ordinal-1]
    if dst is None or dst==root:raise ValueError('direct edge')
    return pc,dst,words[(pc-root)//4]
def summarize(root,words):
    if root&3 or not 1<=len(words)<=1024:raise ValueError('extent')
    loads=stores=backs=conditional=direct=indirect=tail=returns=msr=system=0
    edges=[]
    for i,w in enumerate(words):
        pc=root+4*i;op=w>>26;xo=(w>>1)&1023
        loads+=int(op in (32,33,34,35,40,41,42,43,46,48,49,50,51) or op==31 and xo in (23,55,87,119,279,311,343,375,534))
        stores+=int(op in (36,37,38,39,44,45,47,52,53,54,55) or op==31 and xo in (151,183,215,247,407,439,662))
        if op in (16,18):
            dst=target(pc,w)
            if w&1:direct+=1;edges.append((1,dst))
            else:
                conditional+=int(op==16)
                backs+=int(root<=dst<=pc)
                if not root<=dst<root+4*len(words):tail+=1;edges.append((3,dst))
        if op==19 and xo in (16,528):
            if xo==16 and not w&1:returns+=1
            else:indirect+=1;edges.append((2,None))
        msr+=int(op==31 and xo==146)
        system+=int(op==17 or op==19 and xo==50)
    return dict(words=len(words),loads=loads,stores=stores,backward=backs,conditional=conditional,direct=direct,indirect=indirect,tail=tail,returns=returns,mtmsr=msr,system=system),edges
def inspect(dol,elf):
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n);sizes=parse_functions(elf)
    _,root,_=edge(HANDLER,words,3)
    if not 4<=sizes.get(root,0)<=4096:raise ValueError('third extent')
    code=exact(dol,elf,root,sizes[root]//4)
    summary,edges=summarize(root,code);counts,first=census(root,code)
    known={DISABLE:'disable',RESTORE:'restore',TIME:'time',SCHED:'scheduler',second_plan(dol,elf)[1]:'second',nested_plan(dol,elf)[1]:'nested'}
    print('V740_THIRD_GEOMETRY verified=1 name='+names(elf,root)+' '+' '.join(f'{k}={v}' for k,v in summary.items()))
    print('V740_THIRD_MMIO_PREFIX first_calls='+str(len(first))+' '+' '.join(f'{k}={v}' for k,v in counts.items()))
    for i,(kind,dst) in enumerate(edges,1):
        row=dict(ordinal=i,kind=kind,known=known.get(dst,'other'),exact=0,words=0,direct=0,indirect=0,tail=0,returns=0,mtmsr=0,system=0)
        if dst is not None and 4<=sizes.get(dst,0)<=4096:
            row['exact']=1;child=exact(dol,elf,dst,sizes[dst]//4)
            s,_=summarize(dst,child)
            for k in ('words','direct','indirect','tail','returns','mtmsr','system'):row[k]=s[k]
        print('V740_THIRD_EDGE '+' '.join(f'{k}={v}' for k,v in row.items())+' name='+(names(elf,dst) if dst is not None else 'indirect'))
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError):
        print('V740_THIRD_GEOMETRY verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
