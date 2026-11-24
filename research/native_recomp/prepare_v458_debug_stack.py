#!/usr/bin/env python3
"""Authenticate a bounded stack-only original debug routine, never substitute it."""
import argparse
import hashlib
from pathlib import Path
import struct
from prepare_v453_debug_leaf import DEBUG,BLR,NOP,classify,image
from make_osinit_execparams_v28 import ORIGINAL_SHA,text_at
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions

def signed(n,bits):return n-(1<<bits) if n&(1<<(bits-1)) else n

def validate(words):
    if not 1<=len(words)<=64 or words[-1]!=BLR:raise ValueError('return_geometry')
    for i,w in enumerate(words[:-1]):
        op=w>>26;rs=(w>>21)&31;ra=(w>>16)&31;imm=signed(w&65535,16)
        if w==NOP:continue
        if op==14 and rs==ra==1 and -256<=imm<=256 and imm%4==0:continue
        if op in (36,37,54) and ra==1 and -256<=imm<=256 and imm%(8 if op==54 else 4)==0:
            if op!=37 or rs==1:continue
        # Only forward direct branches; no link, absolute target or CTR
        # mutation. Every path therefore reaches the sole final BLR.
        if op==16 and not w&3 and ((w>>21)&4):
            disp=signed(w&0xfffc,16)
            if 0<disp and i+disp//4<len(words):continue
        if op==18 and not w&3:
            disp=signed(w&0x03fffffc,26)
            if 0<disp and i+disp//4<len(words):continue
        raise ValueError('unsupported_instruction')
    return True

def synthetic_words():
    # Independent test: allocate stack, branch on CR1 EQ, optionally spill
    # two FPRs, spill two GPRs, restore SP, return.
    return (0x9421ffc0,0x4086000c,0xd8210010,0xd8610018,0x90610008,0x90a1000c,0x38210040,BLR)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path)
    p.add_argument('--owner',type=Path);p.add_argument('--elf',type=Path);a=p.parse_args()
    try:
        if a.candidate.exists() or a.candidate.is_symlink() or bool(a.owner)!=bool(a.elf):raise ValueError('destination')
        if a.owner:
            if a.owner.stat().st_size>20_000_000 or a.elf.stat().st_size>64_000_000:raise ValueError('size')
            raw=a.owner.read_bytes();elf=a.elf.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
            sizes=parse_functions(elf);kind,_,count=classify(raw,sizes)
            if kind=='unbounded' or count>64:
                print('V458_DEBUG_SHAPE kind=unsupported words=0 candidate=0 owner=1');return 0
            body=text_at(raw,DEBUG,count*4);words=struct.unpack('>'+str(count)+'I',body)
        else:words=synthetic_words();body=struct.pack('>'+str(len(words))+'I',*words)
        try:validate(words)
        except ValueError:
            print(f'V458_DEBUG_SHAPE kind=unsupported words={len(words)} candidate=0 owner={int(bool(a.owner))}');return 0
        with a.candidate.open('xb') as f:f.write(image(body))
        print(f'V458_DEBUG_SHAPE kind=stack words={len(words)} candidate=1 owner={int(bool(a.owner))}');return 0
    except (OSError,ValueError,struct.error,IndexError):
        print('V458_DEBUG_PREP inspected=0');return 1
if __name__=='__main__':raise SystemExit(main())
