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
    # Classify the immediate request-path leaves and the registered handler
    # region. To avoid exposing original instructions, only emit control
    # flow geometry and bounded read/write width categories.
    for addr in (0x805293b0,0x8051afe0,0x8051905c,0x8051906c,0x805222c0):
        size=funcs.get(addr,0)
        if not 0<size<=MAX_SIZE:raise ValueError("missing V72 dependency")
        code=get_text(raw,addr,size)
        loads=stores=cache=0
        for (op,) in struct.iter_unpack(">I",code):
            major=op>>26
            if major in (32,33,34,35,40,41,42,43):loads+=1
            if major in (36,37,38,39,44,45):stores+=1
            if major==31 and ((op>>1)&1023) in (54,86,246,278,470,982,1014):cache+=1
        print(f"POST72_LEAF addr=0x{addr:08X} size=0x{size:X} loads={loads} stores={stores} cache={cache}")
    # Search only the IPC handler interval already authenticated by V69.
    for addr in sorted(a for a in funcs if 0x80519094<=a<0x805194c4):
        if 0<funcs[addr]<=MAX_SIZE:
            print(f"POST72_IRQ_CANDIDATE addr=0x{addr:08X}")
            describe(raw,funcs,addr)
    # Bounded direct SDA accesses and conditional branch geometry in
    # original send path / init helpers. Never emit opcodes or data values.
    for addr in (0x805194c4,0x8051af28,0x805195ec,0x8051afe0):
        size=funcs.get(addr,0)
        if not 0<size<=MAX_SIZE:raise ValueError("missing V72 send predicate body")
        for i,(op,) in enumerate(struct.iter_unpack(">I",get_text(raw,addr,size))):
            pc=addr+4*i;major=op>>26;ra=(op>>16)&31
            if ra in (2,13) and major in (32,34,40,42,36,38,44):
                offset=op&0xffff
                if offset&0x8000:offset-=0x10000
                print(f"POST72_SDA func=0x{addr:08X} site=0x{pc:08X} base={ra} offset={offset} access={'load' if major in (32,34,40,42) else 'store'}")
            if addr==0x805195ec and major==16:
                disp=op&0xfffc
                if disp&0x8000:disp-=0x10000
                target=(disp if op&2 else pc+disp)&0xffffffff
                print(f"POST72_BRANCH site=0x{pc:08X} target=0x{target:08X}")
    # Identify the external exception and IPC handler transitive frontier.
    # Emit only authenticated function boundaries and edges, not instructions.
    todo=[(0x80526ce0,0),(0x80519318,0),(0x805190c0,0),(0x8052a430,0),(0x8052a51c,0)]
    seen=set()
    while todo and len(seen)<24:
        addr,depth=todo.pop(0)
        if addr in seen or not 0<funcs.get(addr,0)<=MAX_SIZE:continue
        seen.add(addr)
        print(f"POST73_ROOT addr=0x{addr:08X} depth={depth}")
        edges=describe(raw,funcs,addr)
        if depth<1:todo.extend((dst,depth+1) for _,dst in edges if dst not in seen)
    # The external IRQ entry is an assembly trampoline with no BLR.
    # Resolve its direct tail edge, then bound the actual OS dispatcher.
    irq_entry=0x80526ce0
    for i,(op,) in enumerate(struct.iter_unpack(">I",get_text(raw,irq_entry,funcs[irq_entry]))):
        pc=irq_entry+4*i
        if op>>26==18 and not op&1:
            dst=branch_target(op,pc)
            print(f"POST73_TAIL site=0x{pc:08X} target=0x{dst:08X} size=0x{funcs.get(dst,0):X}")
            if 0<funcs.get(dst,0)<=MAX_SIZE and dst not in seen:
                describe(raw,funcs,dst)
                seen.add(dst)
    # Establish whether copying the original vector template into 0x500
    # preserves internal relative branch geometry. No raw instruction bytes.
    template=0x80520ec0
    direct=relative=outside=indirect=0
    for i,(op,) in enumerate(struct.iter_unpack(">I",get_text(raw,template,0x98))):
        pc=template+4*i;major=op>>26
        if major==18:
            direct+=1
            target=branch_target(op,pc)
            if not op&2:
                relative+=1;outside+=not(template<=target<template+0x98)
        elif major==16:
            direct+=1;disp=op&0xfffc
            if disp&0x8000:disp-=0x10000
            if not op&2:
                relative+=1;outside+=not(template<=pc+disp<template+0x98)
        elif major==19 and ((op>>1)&1023) in (16,50,528):indirect+=1
    print(f"POST73_VECTOR bytes=152 direct={direct} relative={relative} outside={outside} indirect={indirect}")
    # Map the original ACK and reply-path scheduler dependencies to depth 1.
    # This is control-flow geometry, not disassembly, instructions or data.
    roots=(0x80519318,0x805190c0,0x8051b060,0x8051b070,
           0x805293f8,0x80529434,0x80529940,0x8052a51c)
    todo=[(a,0) for a in roots];visited=set()
    while todo and len(visited)<24:
        addr,depth=todo.pop(0)
        if addr in visited or not 0<funcs.get(addr,0)<=MAX_SIZE:continue
        visited.add(addr)
        print(f"POST76_ROOT addr=0x{addr:08X} depth={depth}")
        edges=describe(raw,funcs,addr)
        if depth<1:todo.extend((dst,depth+1) for _,dst in edges if dst not in visited)
    # Resolve direct conditional destinations in the two handler bodies.
    # Inspect SDA access geometry without publishing initialized values.
    for addr in (0x80519318,0x805190c0,0x8051b060,0x8051b070,0x805293f8,0x80529434):
        size=funcs[addr]
        for i,(op,) in enumerate(struct.iter_unpack(">I",get_text(raw,addr,size))):
            pc=addr+4*i;major=op>>26;ra=(op>>16)&31
            if major==16:
                disp=op&0xfffc
                if disp&0x8000:disp-=0x10000
                dst=(disp if op&2 else pc+disp)&0xffffffff
                print(f"POST76_BRANCH func=0x{addr:08X} site=0x{pc:08X} target=0x{dst:08X}")
            if ra in (2,13) and major in (32,34,40,42,36,38,44):
                offset=op&0xffff
                if offset&0x8000:offset-=0x10000
                print(f"POST76_SDA func=0x{addr:08X} site=0x{pc:08X} base={ra} offset={offset} access={'load' if major in (32,34,40,42) else 'store'}")
    print("PASS: bounded authenticated post-V69 startup graph")
def main():
    p=argparse.ArgumentParser();p.add_argument("dol",type=Path);p.add_argument("elf",type=Path);a=p.parse_args()
    raw=a.dol.read_bytes();elf=a.elf.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError("owner digest mismatch")
    scan(raw,parse_functions(elf))
if __name__=="__main__":main()
