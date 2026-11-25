#!/usr/bin/env python3
"""Redacted owner-only census of OSInit after the original IRQ-enable return."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v616_irq_enable import RETURN,expectations
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from audit_handler_suffix_v728 import suffix,target
from audit_osinit_v24 import ENTRY,LENGTH
from audit_v264_osinit_retry_elf import CALLSITE as RETRY

# Conservative static classifications. Unknown PPC operations stay unknown,
# and no instruction word, address or data contents appear in the report.
LOAD_XO={23,55,87,119,279,311,343,375,534,790}
STORE_XO={151,183,215,247,407,439,662,918}
def category(w):
    op=w>>26;xo=(w>>1)&1023
    if op==18 and w&3==1:return 'direct'
    if op==16 or op==18:return 'branch'
    if w==0x4e800020:return 'return'
    if op==19 and xo in (16,528,50) or op==17 or op==31 and xo==146:return 'system_control'
    if op in (32,33,34,35,40,41,42,43,46) or op==31 and xo in LOAD_XO:return 'load'
    if op in (36,37,38,39,44,45,47) or op==31 and xo in STORE_XO:return 'store'
    if op in (7,8,10,11,12,13,14,15,20,21,23,24,25,26,27,28,29):return 'integer'
    if op==31 and xo in (0,8,10,19,24,26,28,32,40,60,104,124,136,138,144,200,202,232,234,235,266,284,316,339,412,444,459,467,476,491,536,792,824,922,954):return 'integer'
    return 'other'
def first_region(root,words,start):
    n,backs,stores,stops=suffix(root,words,start)
    terminal={pc:(k,o,dst) for pc,k,o,dst in stops}
    end=root+4*len(words);rows={};todo=[start]
    while todo:
        pc=todo.pop()
        if pc in rows:continue
        if pc&3 or not root<=pc<end or len(rows)>=128:raise ValueError('region extent')
        w=words[(pc-root)//4];rows[pc]=w
        if pc in terminal:
            # Do not pretend a conditional LR return or external branch
            # guarantees the end of the fallthrough path.
            if terminal[pc][0] not in (1,3,5,6):raise ValueError('unsupported boundary')
            continue
        op=w>>26
        if op in (16,18):
            if w&3:raise ValueError('branch geometry')
            todo.append(target(pc,w))
            if op==18:continue
        todo.append(pc+4)
    if len(rows)!=n:raise ValueError('region coverage')
    return rows,backs,stores,stops
def plan(dol,elf):
    expectations(dol,elf)
    sizes=parse_functions(elf)
    if sizes.get(ENTRY)!=LENGTH or not ENTRY<=RETURN<ENTRY+LENGTH:raise ValueError('OSInit extent')
    words=exact(dol,elf,ENTRY,LENGTH//4)
    rows,backs,stores,stops=first_region(ENTRY,words,RETURN)
    # A second static window begins after each initial linked call, but no
    # new call is admitted or assumed to return in the first-region result.
    targets=[]
    for pc,k,o,dst in stops:
        size=sizes.get(dst,0)
        if k==1 and (not size or size>32768 or size&3):raise ValueError('dependency extent')
        if k==1:exact(dol,elf,dst,min(size//4,1))
        targets.append((k,o,size//4,int(pc==RETRY),int(pc<RETRY)))
    return rows,backs,stores,targets
def report(rows,backs,stores,targets):
    kinds=('integer','load','store','branch','direct','return','system_control','other')
    values={k:0 for k in kinds}
    for w in rows.values():values[category(w)]+=1
    print(f'V929_OSINIT_REGION verified=1 labels={len(rows)} backward={backs} stores={stores} boundaries={len(targets)} execution=0')
    print('V929_OSINIT_CLASSES '+' '.join(f'{k}={values[k]}' for k in kinds))
    for i,(k,o,n,retry,before) in enumerate(targets,1):
        print(f'V929_OSINIT_BOUNDARY ordinal={i} kind={k} call_ordinal={o} target_words={n} retry_helper={retry} before_retry={before}')
    # Only first straight-line sequence is enumerated by class. Stop at
    # first branch or terminal. No private encodings or locations.
    start=min(rows)
    if start not in rows:return
    for i in range(min(32,len(rows))):
        w=rows.get(start+4*i)
        if w is None:break
        k=category(w);print(f'V929_OSINIT_PREFIX visit={i+1} kind={k}')
        if k in ('branch','direct','return','system_control'):break
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        report(*plan(a.dol.read_bytes(),a.elf.read_bytes()))
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError) as e:
        safe=('region extent','unsupported boundary','branch geometry','region coverage','OSInit extent','dependency extent','fallthrough','extent')
        print('V929_OSINIT_REGION verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
