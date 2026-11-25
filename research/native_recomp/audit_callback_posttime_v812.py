#!/usr/bin/env python3
"""Private callback post-time dependency graph; only SDK allowlist names and counts."""
import argparse
import struct
from collections import deque
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE,TIME
from make_private_elf_symbol_map import parse_functions
from audit_callback_deps_v787 import CALLBACK
from audit_callback_frontiers_v799 import call_sites,continuations
from audit_handler_third_v740 import names,summarize,KNOWN
from audit_handler_deps_v749 import graph
from audit_si_deep_v695 import census
from audit_handler_suffix_v728 import suffix
from si_nested_geometry_v693 import nested_plan

SDK=tuple(sorted(set(KNOWN+(
    'OSGetWirelessID','OSSetWirelessID','OSGetWirelessPadID','OSSetWirelessPadID',
    'OSGetGbsMode','OSSetGbsMode','OSGetSoundMode','OSSetSoundMode',
    '__OSLockSram','__OSLockSramEx','__OSUnlockSram','__OSUnlockSramEx',
    '__OSSyncSram','__OSInitSram','__OSReadSram','__OSWriteSram',
    'LockSram','UnlockSram','ReadSram','WriteSram','WriteSramCallback','WriteSramCallback0',
    '__OSReadROM','EXILock','EXIUnlock','EXISelect','EXIDeselect','EXIImm','EXIImmEx',
    'EXIDma','EXISync','EXIProbe','EXIProbeEx','EXIGetState','EXIGetID',
    'EXIGetType','EXIGetTypeString','EXIAttach','EXIDetach','EXISetExiCallback',
    'EXIClearInterrupts','EXISetInterruptMask','EXIInterruptHandler','TCInterruptHandler',
    '__EXIProbe','__EXIGetID','__EXILock','__EXIUnlock','__EXISelect',
    'OSReport','OSPanic','memcpy','memset','DCInvalidateRange','DCFlushRange'
))))

def first_roots(root,words):
    sites=call_sites(root,words)
    if len(words)!=172 or len(sites)!=13 or [i for i,(_,k,_) in enumerate(sites,1) if k==2]!=[4,12]:
        raise ValueError('callback shape')
    if continuations(root,words)[2][4]!=(3,5):
        raise ValueError('time frontier')
    a,b=sites[2][2],sites[4][2]
    if not a or not b or a==b or any(sites[i-1][2]!=a for i in (7,9,11)):
        raise ValueError('callback dependency groups')
    return a,b

def shared(a,aw,b,bw):
    ea=graph(a,aw);eb=graph(b,bw)
    if len(aw)!=39 or len(bw)!=30 or len(ea)!=4 or len(eb)!=3:
        raise ValueError('dependency geometry')
    if any(k!=1 for k,_ in ea+eb) or [x for _,x in ea[:2]]!=[DISABLE,RESTORE] or [x for _,x in eb[:2]]!=[DISABLE,RESTORE]:
        raise ValueError('dependency interrupt leaves')
    dst=ea[2][1]
    if dst is None or ea[3][1]!=dst or eb[2][1]!=dst or dst in (a,b,DISABLE,RESTORE):
        raise ValueError('shared dependency identity')
    return dst

def collect(dol,elf,roots,sizes,max_nodes=40,max_depth=2):
    ids={a:i+1 for i,a in enumerate(roots)}
    queue=deque((a,0) for a in roots)
    emitted=set()
    known={DISABLE:1,RESTORE:2,TIME:3,nested_plan(dol,elf)[1]:4,CALLBACK:5}
    while queue:
        a,depth=queue.popleft()
        if a in emitted:continue
        emitted.add(a)
        n=sizes.get(a,0)
        if n<4 or n>4096 or n&3:raise ValueError('root extent')
        ws=exact(dol,elf,a,n//4)
        s,edges=summarize(a,ws)
        c,first=census(a,ws)
        name=names(elf,a,SDK)
        print(f'V812_CALLBACK_DEP root={ids[a]} depth={depth} known={known.get(a,0)} name={name} '+' '.join(f'{k}={v}' for k,v in s.items()))
        print(f'V812_CALLBACK_DEP_PREFIX root={ids[a]} first_calls={len(first)} '+' '.join(f'{k}={v}' for k,v in c.items()))
        for i,(kind,dst) in enumerate(edges,1):
            z=sizes.get(dst,0)
            exact_root=bool(4<=z<=4096 and not z&3)
            if exact_root:
                exact(dol,elf,dst,z//4)
                if dst not in ids:
                    if len(ids)>=max_nodes:raise ValueError('dependency bound')
                    ids[dst]=len(ids)+1
                    if depth<max_depth and dst not in known:queue.append((dst,depth+1))
            nm=names(elf,dst,SDK) if dst is not None else 'indirect'
            print(f'V812_CALLBACK_DEP_EDGE root={ids[a]} edge={i} kind={kind} child={ids.get(dst,0)} known={known.get(dst,0)} exact={int(exact_root)} words={z//4 if exact_root else 0} name={nm}')
        # All reachable linked-call frontiers, not proof of runtime choice.
        sites=call_sites(a,ws)
        if len(sites)>32:raise ValueError('call bound')
        for i,start in enumerate([a]+[pc+4 for pc,_,_ in sites]):
            if start>=a+4*len(ws):continue
            labels,backs,stores,stops=suffix(a,ws,start)
            callmask=sum(1<<(j-1) for j in {o for _,k,o,_ in stops if k in (1,5) and o})
            exits=tuple(sum(k==t for _,k,_,_ in stops) for t in (2,3,4,6))
            print(f'V812_CALLBACK_DEP_FRONTIER root={ids[a]} after={i} labels={labels} backward={backs} stores={stores} call_mask={callmask} tail={exits[0]} returns={exits[1]} indirect_exit={exits[2]} system={exits[3]}')
    return len(emitted),len(ids)

def inspect(dol,elf):
    sizes=parse_functions(elf)
    if sizes.get(CALLBACK)!=688:raise ValueError('callback extent')
    a,b=first_roots(CALLBACK,exact(dol,elf,CALLBACK,172))
    if sizes.get(a)!=156 or sizes.get(b)!=120:raise ValueError('wrapper extent')
    c=shared(a,exact(dol,elf,a,39),b,exact(dol,elf,b,30))
    if sizes.get(c)!=736:raise ValueError('shared extent')
    exact(dol,elf,c,184)
    count,ids=collect(dol,elf,(a,b,c),sizes)
    print(f'V812_CALLBACK_POSTTIME_CENSUS verified=1 wrapper_groups=2 shared_root=1 inspected={count} exact_roots={ids} dynamic_target=0 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('callback shape','time frontier','callback dependency groups','callback extent','wrapper extent','dependency geometry','dependency interrupt leaves','shared dependency identity','shared extent','root extent','dependency bound','call bound','unsupported call form','fallthrough')
        print('V812_CALLBACK_POSTTIME_CENSUS verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
