#!/usr/bin/env python3
"""Conservative, original-only r9/r10 read-before-definition analysis.

Follow both sides of every conditional branch and actual callees. No
ABI-clobber assumption is made. Unsupported live instructions refuse
the proof. Only bounded numeric census is public.
"""
import argparse
import struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_v765 import plan

BLR=0x4e800020
TRACKED=(9,10)
def mask(regs):
    return sum(1<<i for i,r in enumerate(TRACKED) if r in regs)

def effect(w):
    """Return conservative GPR read/write sets, or None for unsupported."""
    op=w>>26;rt=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;xo=(w>>1)&1023
    a={ra} if ra else set()
    if op in (7,8,12,13):return {ra},{rt}
    if op in (14,15):return a,{rt}
    if op in (10,11):return {ra},set()
    if op in (24,25,26,27,28,29):return {rt},{ra}
    if op==20:return {rt,ra},{ra}
    if op==21:return {rt},{ra}
    if op==23:return {rt,rb},{ra}
    if op in (32,34,40,42):return a,{rt}
    if op in (33,35,41,43):
        if not ra or ra==rt:return None
        return {ra},{rt,ra}
    if op in (36,38,44):return a|{rt},set()
    if op in (37,39,45):
        if not ra:return None
        return {ra,rt},{ra}
    if op==46:return a,set(range(rt,32))
    if op==47:return a|set(range(rt,32)),set()
    if op in (48,50,52,54):return a,set()
    if op in (49,51,53,55):
        return ({ra},{ra}) if ra else None
    if op==19 and xo in (0,33,129,193,225,257,289,417,449,150):return set(),set()
    if op!=31:return None
    if xo in (0,32):return {ra,rb},set()
    if xo in (19,83,339,371):return set(),{rt}
    if xo in (144,146,467):return {rt},set()
    if xo==512:return set(),set() # mcrxr
    if xo in (28,60,124,284,316,412,444,476,24,536,792):return {rt,rb},{ra}
    if xo in (26,922,954,824):return {rt},{ra}
    if xo in (23,87,279,343,534,790,20):return a|{rb},{rt}
    if xo in (55,119,311,375):
        if not ra or ra==rt:return None
        return {ra,rb},{rt,ra}
    if xo in (151,215,407,662,918,150):return a|{rb,rt},set()
    if xo in (183,247,439):
        return ({ra,rb,rt},{ra}) if ra else None
    if xo in (54,86,246,278,470,982,1014):return a|{rb},set()
    if xo in (598,854):return set(),set()
    # OE is legal for these integer arithmetic families only.
    if (xo&511) in (8,10,40,136,138,235,266,459,491):return {ra,rb},{rt}
    if (xo&511) in (104,200,202,232,234):return {ra},{rt}
    if xo in (11,75):return {ra,rb},{rt}
    return None

def target(pc,w):
    op=w>>26;bits,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
    return ((0 if w&2 else pc)+(((w&bits)^sign)-sign))&0xffffffff

def analyze(roots,root,edges):
    if root not in roots or not 1<=len(roots)<=8 or len(edges)>16:
        raise ValueError('geometry')
    owners={};code={}
    for start,words in roots.items():
        if start&3 or not 1<=len(words)<=1024:raise ValueError('geometry')
        for i,w in enumerate(words):
            pc=start+4*i
            if pc in code:raise ValueError('overlap')
            code[pc]=w;owners[pc]=start
    links=dict(edges)
    if len(links)!=len(edges) or any(site not in code or dst not in roots or code[site]>>26!=18 or code[site]&3!=1 or target(site,code[site])!=dst for site,dst in links.items()):
        raise ValueError('edges')
    stack=[(root,(),3)];seen=set();killed=returns=unsupported=read=0
    while stack:
        pc,ret,live=stack.pop()
        state=(pc,ret,live)
        if state in seen:continue
        seen.add(state)
        if len(seen)>16384 or len(ret)>8:raise ValueError('bound')
        if not live:killed+=1;continue
        if pc not in code:unsupported+=1;continue
        w=code[pc];op=w>>26;xo=(w>>1)&1023
        if pc in links:
            if owners.get(pc+4)!=owners[pc]:unsupported+=1;continue
            stack.append((links[pc],ret+(pc+4,),live));continue
        if w==BLR:
            if ret:stack.append((ret[-1],ret[:-1],live))
            else:returns+=1
            continue
        if op in (16,18):
            if w&1:unsupported+=1;continue
            dst=target(pc,w)
            if owners.get(dst)!=owners[pc]:unsupported+=1;continue
            stack.append((dst,ret,live))
            if op==16:
                if owners.get(pc+4)!=owners[pc]:unsupported+=1
                else:stack.append((pc+4,ret,live))
            continue
        if op==17 or (op==19 and xo in (16,50,528)):
            unsupported+=1;continue
        e=effect(w)
        if e is None:unsupported+=1;continue
        reads,writes=e
        hazard=mask(reads)&live
        if hazard:read|=hazard;continue
        if owners.get(pc+4)!=owners[pc]:unsupported+=1;continue
        stack.append((pc+4,ret,live&~mask(writes)))
    proven=not unsupported and not read and bool(killed or returns)
    return proven,len(seen),killed,returns,unsupported,read

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        roots,C,D,Q,S,R,edges=plan(a.dol.read_bytes(),a.elf.read_bytes())
        ok,states,killed,returns,unknown,read=analyze({k:roots[k] for k in (C,D,Q,S,R)},C,edges)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError,StopIteration):
        print('V1042_ABI_LIVENESS inspected=0');return 1
    print(f'V1042_ABI_LIVENESS inspected=1 proven={int(ok)} states={states} killed={killed} root_returns={returns} unsupported={unknown} read_mask={read} original_execution=0')
    # Inconclusive static proof does not invalidate the already-verified
    # differential execution; it simply leaves that evidence bounded.
    return 0
if __name__=='__main__':raise SystemExit(main())
