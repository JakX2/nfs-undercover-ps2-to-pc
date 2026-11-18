#!/usr/bin/env python3
"""Bounded authenticated metadata of the startup tail following IPCCltInit."""
import argparse,hashlib,struct
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from probe_next_osinit_v33 import classify,branch_target
from probe_post_v68 import describe,MAX_SIZE
START=0x8052094c
STOP=0x80520980
CALLS=((0x80520964,0x8052b034),(0x80520968,0x8052f790),(0x8052096c,0x8052f830),(0x80520978,0x8052be14))
def scan(raw,funcs):
    span=get_text(raw,START,STOP-START)
    counts,calls=classify(span,START)
    if calls!=list(CALLS):raise ValueError("post IPC call graph mismatch")
    print(f"POST69_RANGE start=0x{START:08X} end=0x{STOP:08X}")
    for i,(op,) in enumerate(struct.iter_unpack(">I",span)):
        pc=START+i*4
        if op>>26==16:
            disp=op&0xfffc
            if disp&0x8000:disp-=0x10000
            target=(disp if op&2 else pc+disp)&0xffffffff
            print(f"POST69_BRANCH site=0x{pc:08X} target=0x{target:08X}")
        elif op>>26==18 and not op&1:
            print(f"POST69_BRANCH site=0x{pc:08X} target=0x{branch_target(op,pc):08X}")
    seen=set()
    for site,target in calls:
        print(f"POST69_ROOT site=0x{site:08X} target=0x{target:08X} size=0x{funcs.get(target,0):X}")
        if target not in seen:
            seen.add(target)
            edges=describe(raw,funcs,target)
            for child in dict.fromkeys(dst for _,dst in edges):
                if len(seen)>=16:break
                if child not in seen and 0<funcs.get(child,0)<=MAX_SIZE:
                    seen.add(child)
                    describe(raw,funcs,child)
    # The next native request lane needs the descendants of IOS_Open's
    # synchronous submission helper, not a guessed replacement return.
    # The graph is bounded to 12 distinct function bodies and two layers.
    frontier=[(0x805195ec,0)]
    visited=set()
    while frontier and len(visited)<12:
        addr,depth=frontier.pop(0)
        if addr in visited or not 0<funcs.get(addr,0)<=MAX_SIZE:continue
        visited.add(addr)
        print(f"POST71_DISCOVERY addr=0x{addr:08X} depth={depth}")
        edges=describe(raw,funcs,addr)
        if depth<2:
            frontier.extend((dst,depth+1) for _,dst in edges if dst not in visited)
    # Resolve the four-byte IOS_Open dependency without disclosing the
    # owner instruction word. A tail branch requires its full target body.
    leaf=0x8051ad38
    op=struct.unpack(">I",get_text(raw,leaf,4))[0]
    if op==0x4e800020:
        print("POST71_LEAF kind=return target=0x00000000 size=0x0")
    elif op>>26==18:
        dst=branch_target(op,leaf)
        print(f"POST71_LEAF kind={'call' if op&1 else 'tail'} target=0x{dst:08X} size=0x{funcs.get(dst,0):X}")
        if 0<funcs.get(dst,0)<=MAX_SIZE:describe(raw,funcs,dst)
    elif op==0x60000000:
        print("POST71_LEAF kind=nop target=0x00000000 size=0x0")
    else:
        print("POST71_LEAF kind=other target=0x00000000 size=0x0")
    print("PASS: bounded authenticated post-V69 startup graph")
def main():
    p=argparse.ArgumentParser();p.add_argument("dol",type=Path);p.add_argument("elf",type=Path);a=p.parse_args()
    raw=a.dol.read_bytes();elf=a.elf.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError("owner digest mismatch")
    scan(raw,parse_functions(elf))
if __name__=="__main__":main()
