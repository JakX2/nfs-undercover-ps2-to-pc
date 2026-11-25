#!/usr/bin/env python3
"""Bounded owner-only handler suffix census, no original PCs/words in output."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,words_at
from prepare_v668_si_ack import geometry,HANDLER,shape
from prepare_v667_si_dispatch import exact
from si_second_geometry_v688 import second_plan
from make_private_elf_symbol_map import parse_functions
from classify_save_leaf_v683 import symbol_evidence

def target(pc,w):
    op=w>>26;mask,sign=(0xfffc,0x8000) if op==16 else (0x3fffffc,0x2000000)
    disp=((w&mask)^sign)-sign
    return ((0 if w&2 else pc)+disp)&0xffffffff

def suffix(root,words,start):
    end=root+4*len(words)
    if root&3 or not 1<=len(words)<=1024 or start&3 or not root<=start<end:raise ValueError('extent')
    _,direct,indirect=shape(root,words)
    ordinals={pc:i+1 for i,pc in enumerate(sorted([p for p,_ in direct]+list(indirect)))}
    seen=set();work=[start];stops=[];backs=set();stores=0
    while work:
        pc=work.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<end:raise ValueError('fallthrough')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op in (36,37,38,39,44,45,47) or op==31 and xo in (151,183,215,247,407,439,662):stores+=1
        if op in (16,18):
            dst=target(pc,w)
            if w&1:stops.append((pc,1,ordinals.get(pc,0),dst));continue
            if not root<=dst<end:stops.append((pc,2,0,dst))
            else:
                work.append(dst)
                if dst<=pc:backs.add(pc)
            if op==18:continue
        elif op==19 and xo in (16,528):
            kind=3 if w==0x4e800020 else 4 if xo==16 and not(w&1) else 5
            stops.append((pc,kind,ordinals.get(pc,0),None))
            if kind==4 and ((w>>21)&20)!=20:work.append(pc+4)
            continue
        elif op==17 or (op==19 and xo==50) or (op==31 and xo==146):
            stops.append((pc,6,0,None));continue
        work.append(pc+4)
    return len(seen),len(backs),stores,sorted(stops)

def restore_suffix(words):
    # Conservative recognizer: only contiguous nonvolatile GPR loads
    # from one negative stack/frame offset, with a final canonical BLR.
    if not 2<=len(words)<=19 or words[-1]!=0x4e800020:return 0
    first=words[0];base=(first>>16)&31;reg=(first>>21)&31;disp=((first&0xffff)^0x8000)-0x8000
    if first>>26!=32 or base not in (1,11) or not 14<=reg<=31 or len(words)!=33-reg or disp>=0 or disp<-512 or disp&3:return 0
    for i,w in enumerate(words[:-1]):
        if w>>26!=32 or (w>>16)&31!=base or (w>>21)&31!=reg+i or ((w&0xffff)^0x8000)-0x8000!=disp+4*i or disp+4*i>=0:return 0
    return 32-reg

def classify_target(dol,elf,dst,sizes):
    if dst is None:return (0,0,0,0)
    size=sizes.get(dst,0);owners=sum(a<dst<a+n for a,n in sizes.items());rest=0
    if size and size<=4096 and not size&3:
        code=exact(dol,elf,dst,size//4);rest=restore_suffix(code)
    elif owners==1:
        for n in range(1,20):
            try:code=exact(dol,elf,dst,n)
            except ValueError:break
            if code[-1]==0x4e800020:
                rest=restore_suffix(code);break
    ev=symbol_evidence(elf,dst)
    return (int(bool(size)),min(owners,9),rest,int(bool(ev['zero_func'] or ev['notype'])))

def inspect(dol,elf):
    n,*_=geometry(dol,elf);site,*_=second_plan(dol,elf);words=exact(dol,elf,HANDLER,n)
    labels,backs,stores,stops=suffix(HANDLER,words,site+4)
    sizes=parse_functions(elf)
    rows=[(i,kind,ordinal,*classify_target(dol,elf,dst,sizes)) for i,(_,kind,ordinal,dst) in enumerate(stops,1)]
    return labels,backs,stores,rows

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        labels,backs,stores,rows=inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError):
        print('V728_HANDLER_SUFFIX inspected=0');return 1
    print(f'V728_HANDLER_SUFFIX inspected=1 reachable={labels} backward={backs} stores={stores} boundaries={len(rows)} execution=0')
    for i,kind,ordinal,root,owners,restore,symbol in rows:
        print(f'V728_HANDLER_BOUNDARY ordinal={i} kind={kind} call_ordinal={ordinal} exact_root={root} containing={owners} restore_gprs={restore} alias_symbol={symbol}')
    return 0
if __name__=='__main__':raise SystemExit(main())
