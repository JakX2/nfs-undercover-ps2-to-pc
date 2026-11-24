#!/usr/bin/env python3
"""Authenticate the original debug routine and its exception callsites.
Only a complete, exact NOP/BLR leaf is eligible for the native leaf test.
Never publish owner instructions, vector offsets, names or private paths.
"""
import argparse
import hashlib
from pathlib import Path
import struct
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at,target
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

DEBUG=0x804e50b8
SITES=(0x80520c44,0x80520cdc,0x80520d08,0x80520e58)
VECTORS=0x8060bbe0
NOP=0x60000000
BLR=0x4e800020

def image(body,pc=DEBUG):
    if not body or len(body)%4 or not 0x80004000<=pc<0x81800000 or pc&3 or pc+len(body)>0x81800000:
        raise ValueError('geometry')
    out=bytearray(256)
    for off,val in ((0,256),(0x48,pc),(0x90,len(body)),(0xe0,pc)):struct.pack_into('>I',out,off,val)
    return bytes(out)+body

def data_at(raw,pc,n):
    if pc&3 or n<=0 or n&3:raise ValueError('data geometry')
    hits=[]
    for i in range(11):
        off,base,size=(struct.unpack_from('>I',raw,h+4*i)[0] for h in (0x1c,0x64,0xac))
        if size and base<=pc and pc+n<=base+size:
            where=off+pc-base
            if off<256 or off+size>len(raw):raise ValueError('data bounds')
            hits.append(raw[where:where+n])
    if len(hits)!=1:raise ValueError('data mapping')
    return hits[0]

def vector_geometry(raw):
    try:offsets=struct.unpack('>15I',data_at(raw,VECTORS,60))
    except (ValueError,struct.error):return False,False
    spans=sorted((x,x+0x98) for x in offsets)
    ok=all(0x100<=a and b<=0x3000 and not a&31 for a,b in spans) and all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
    return ok,0xc00 in offsets

def classify(owner,sizes):
    for site in SITES:
        word=struct.unpack('>I',text_at(owner,site,4))[0]
        if target(word,site,True)!=DEBUG:raise ValueError('callsite')
    n=sizes.get(DEBUG,0)
    if not n or n%4 or n>4096:return 'unbounded',None,0
    body=text_at(owner,DEBUG,n);words=struct.unpack('>'+str(n//4)+'I',body)
    if len(words)<=32 and words[-1]==BLR and all(w==NOP for w in words[:-1]):
        return 'leaf',image(body),len(words)
    # A leaf with side effects or more complex control flow must not be
    # treated as a no-op. Report shape only, without publishing its words.
    calls=any(w>>26==18 and w&1 or w>>26==19 and ((w>>1)&1023)==528 and w&1 for w in words)
    return ('linked' if calls else 'other'),None,len(words)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate',type=Path)
    p.add_argument('--owner',type=Path);p.add_argument('--elf',type=Path)
    a=p.parse_args()
    try:
        if a.candidate.exists() or a.candidate.is_symlink() or bool(a.owner)!=bool(a.elf):raise ValueError('destination or input pair')
        if a.owner:
            if a.owner.stat().st_size>20_000_000 or a.elf.stat().st_size>64_000_000:raise ValueError('size')
            owner=a.owner.read_bytes();elf=a.elf.read_bytes()
            if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
            kind,candidate,words=classify(owner,parse_functions(elf))
            table,syscall=vector_geometry(owner)
            print(f'V453_EXCEPTION_TABLE mapped_nonoverlap={int(table)} syscall_slot={int(syscall)}')
        else:
            kind='leaf';words=3;candidate=image(struct.pack('>III',NOP,NOP,BLR))
        if candidate is not None:
            with a.candidate.open('xb') as f:f.write(candidate)
        print(f'V453_DEBUG_SHAPE kind={kind} words={words} candidate={int(candidate is not None)} owner={int(bool(a.owner))}')
        return 0
    except (OSError,ValueError,struct.error,IndexError):
        print('V453_DEBUG_PREP inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
