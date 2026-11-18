#!/usr/bin/env python3
"""Owner-local bounded metadata for the verified V90 subsystem's direct children."""
import argparse,hashlib,struct
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from probe_post_v68 import describe,MAX_SIZE
from probe_next_osinit_v33 import classify
from make_start_to_ipc_ack_v77 import make as fixture

ROOT=0x8051e5bc
NODES=(0x8054b114,0x8051f634,0x8051e5b8,0x8051e5bc)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("dol",type=Path);p.add_argument("elf",type=Path);a=p.parse_args()
    raw=a.dol.read_bytes();elf=a.elf.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("owner digest mismatch")
    funcs=parse_functions(elf)
    old=fixture(a.dol)
    for i in range(7):
        base,n=(struct.unpack_from(">I",old,k+4*i)[0] for k in (0x48,0x90))
        print(f"V99_REGION index={i} begin=0x{base:08X} end=0x{base+n:08X}")
    _,calls=classify(get_text(raw,ROOT,funcs[ROOT]),ROOT)
    if not set(NODES[:3])<=set(x[1] for x in calls):
        raise ValueError("original direct subsystem graph differs")
    seen=set()
    todo=list(NODES)
    for node in todo:
        if node in seen or len(seen)>=24 or not 0<funcs.get(node,0)<=MAX_SIZE:continue
        _,edges=classify(get_text(raw,node,funcs[node]),node)
        if len(edges)>24:continue
        seen.add(node)
        describe(raw,funcs,node)
        if node in (NODES[0],NODES[1],ROOT):
            todo.extend(t for _,t in edges if t not in todo)
        for i,(word,) in enumerate(struct.iter_unpack(">I",get_text(raw,node,funcs[node]))):
            major=word>>26;ra=(word>>16)&31
            if ra in (2,13) and major in (32,34,40,42,36,38,44):
                off=word&0xffff
                if off&0x8000:off-=0x10000
                print(f"V99_SDA func=0x{node:08X} site=0x{node+4*i:08X} base={ra} offset={off} access={'load' if major in (32,34,40,42) else 'store'}")
    print("PASS: bounded authenticated V99 final NAND helper dependency metadata")
if __name__=="__main__":main()
