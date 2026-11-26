#!/usr/bin/env python3
"""V264: private owner Wii ELF control-flow classification, never code export."""
import argparse
import hashlib
import struct
import sys
from pathlib import Path
from functools import lru_cache
from audit_v243_original_callback_branch import branch_target
from make_private_elf_symbol_map import HEADER, SECTION, ORIGINAL_SHA256, parse_functions

CALLSITE=0x8052096c
HELPER=0x8052f830
DISABLE=0x805265ac
RESTORE=0x805265d4
GETTIME=0x8052a824
ERRORS={"digest","symbols","caller","helper","section","geometry"}

@lru_cache(maxsize=2)
def _text_sections(data:bytes)->tuple[tuple[int,int,int],...]:
    h=HEADER.unpack_from(data)
    off,unit,n=h[6],h[11],h[12]
    if unit!=SECTION.size or n<1 or n>9999 or off+n*unit>len(data):
        raise ValueError("section")
    rows=[]
    for i in range(n):
        _,kind,flags,base,fo,size,*_=SECTION.unpack_from(data,off+i*unit)
        if kind!=8 and flags&4 and fo+size<=len(data):
            rows.append((base,fo,size))
    return tuple(rows)

def read_words(data:bytes,addr:int,count:int)->list[int]:
    if not 0<count<=8192 or addr&3:raise ValueError("geometry")
    # Cache only immutable file bytes, in-process. Mutable synthetic input
    # must be validated again. Keep the existing unique-section contract.
    rows=_text_sections(data) if type(data) is bytes else _text_sections.__wrapped__(data)
    matches=[fo+addr-base for base,fo,size in rows if base<=addr and addr+4*count<=base+size]
    if len(matches)!=1:raise ValueError("section")
    return list(struct.unpack_from(">"+str(count)+"I",data,matches[0]))

def classify(start:int,caller:list[int],helper:list[int])->dict[str,int]:
    if start>CALLSITE or (CALLSITE-start)&3 or (CALLSITE-start)//4>=len(caller):
        raise ValueError("geometry")
    idx=(CALLSITE-start)//4
    word=caller[idx]
    tail=[(start+4*j,caller[j]) for j in range(idx+1,min(len(caller),idx+65))]
    if len(tail)<8:raise ValueError("geometry")
    branches=[(pc,word>>26,branch_target(pc,word)) for pc,word in tail]
    back=[(pc,dest) for pc,op,dest in branches if dest is not None and start<=dest<=pc]
    targets=[branch_target(HELPER+4*i,w) for i,w in enumerate(helper)]
    return dict(
        direct=int(word>>26==18 and branch_target(CALLSITE,word)==HELPER),
        link=int(bool(word&1)),
        window=len(tail),
        cond=sum(op==16 for _,op,_ in branches),
        backward=len(back),
        back_to_call=sum(dest<=CALLSITE for _,dest in back),
        back_cond=sum(op==16 and dest is not None and start<=dest<=pc
                      for pc,op,dest in branches),
        compare=sum((w>>26 in (10,11)) or
                    (w>>26==31 and ((w>>1)&1023) in (0,32)) for _,w in tail),
        loads=sum(w>>26 in (32,33,34,35,40,41,42,43) for _,w in tail),
        stores=sum(w>>26 in (36,37,38,39,44,45) for _,w in tail),
        sda_loads=sum(w>>26 in (32,33,34,35,40,41,42,43)
                      and ((w>>16)&31)==13 for _,w in tail),
        sc_sda=sum(w>>26 in (32,33,34,35,40,41,42,43)
                   and ((w>>16)&31)==13 and (w&0xffff)==((-3176)&0xffff)
                   for _,w in tail),
        sc_byte=sum(w>>26==34 and ((w>>16)&31)==13
                    and (w&0xffff)==((-3176)&0xffff) for _,w in tail),
        disable=sum(t==DISABLE for t in targets),
        restore=sum(t==RESTORE for t in targets),
        gettime=sum(t==GETTIME for t in targets),
        mftb=sum(w>>26==31 and ((w>>1)&1023)==371 for w in helper),
        back_span=min((pc-dest for pc,dest in back),default=0)
    )

def private_audit(data:bytes)->dict[str,int]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000:raise ValueError("symbols")
    owners=[(pc,n) for pc,n in functions.items()
            if 0x80400000<=pc<0x80600000 and pc<=CALLSITE and CALLSITE+4<=pc+n]
    if len(owners)!=1:raise ValueError("caller")
    base,size=owners[0]
    length=functions.get(HELPER,0)
    if length<16 or length>32768 or length&3:raise ValueError("helper")
    return classify(base,read_words(data,base,size//4),
                    read_words(data,HELPER,length//4))

def format_result(v:dict[str,int])->str:
    keys=("direct","link","window","cond","backward","back_to_call",
          "back_cond","compare","loads","stores","sda_loads","sc_sda",
          "sc_byte","disable","restore","gettime","mftb","back_span")
    return "V264_LOOP_STRUCT owner=1 " + " ".join(f"{k}={v[k]}" for k in keys)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_elf",type=Path)
    a=p.parse_args()
    try: stats=private_audit(a.owner_elf.read_bytes())
    except (OSError,ValueError) as exc:
        kind=str(exc)
        if kind not in ERRORS:kind="symbols"
        print("V264_AUDIT_ERROR kind="+kind,file=sys.stderr)
        return 1
    print(format_result(stats))
    print("V264_ORIGINAL_ELF verified=1")
    return 0

if __name__=="__main__":
    sys.exit(main())
