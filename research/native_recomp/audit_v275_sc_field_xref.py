#!/usr/bin/env python3
"""V275: authenticated Wii ELF +0x188 structure field read/write candidates.

An identical D-form displacement does NOT prove two instructions use
the same object. This read-only audit reports the four verified
lwz +0x188 -> stb SYSCONF edges plus candidate field writers,
restricted to sanitized owner/function metadata.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import struct
import sys

from audit_v264_osinit_retry_elf import read_words
from audit_v268_sc_status_writers import access,owners
from make_private_elf_symbol_map import HEADER,SECTION,ORIGINAL_SHA256,parse_functions

FIELD=0x188
SC_WRITERS=(0x80530ba0,0x80530dbc)
RELEVANT_LO=0x8052e000
RELEVANT_HI=0x80532000

def field_access(word:int)->str:
    op=word>>26
    if (word&0xffff)!=FIELD or ((word>>16)&31)==0:
        return "other"
    return {32:"load",36:"write_word",38:"write_byte",44:"write_half"}.get(op,"other")


def input_edges(owner:int,words:list[int])->list[tuple[int,int,int,int]]:
    """(store offset, load offset, load base rA, loaded register rT)."""
    if owner not in SC_WRITERS or len(words)>8192:
        raise ValueError("geometry")
    matches=[]
    for idx,word in enumerate(words):
        if access(word)!="byte_write" or not idx:continue
        prior=words[idx-1]
        if field_access(prior)!="load":continue
        rt=(prior>>21)&31
        if rt!=(word>>21)&31:continue
        matches.append((idx*4,(idx-1)*4,(prior>>16)&31,rt))
    return matches


def scan_executable(data:bytes,functions:dict[int,int])->tuple[dict[str,int],Counter]:
    head=HEADER.unpack_from(data)
    off,unit,count=head[6],head[11],head[12]
    if unit!=SECTION.size or not 0<count<10000 or off+count*unit>len(data):
        raise ValueError("sections")
    locations=[]
    sections=0
    for i in range(count):
        _,kind,flags,base,pos,size,*_=SECTION.unpack_from(data,off+i*unit)
        if kind==8 or not flags&4:continue
        if base&3 or pos&3 or size&3 or not 0<size<=16*1024*1024 or pos+size>len(data):
            raise ValueError("section_bounds")
        sections+=1
        for ix,(word,) in enumerate(struct.iter_unpack(">I",data[pos:pos+size])):
            k=field_access(word)
            if k!="other":locations.append((base+4*ix,k))
    if not 0<sections<=32:raise ValueError("sections")
    mapped=owners(locations,functions)
    typecount=Counter(kind for _,kind in mapped)
    writes=Counter(owner for owner,kind in mapped if kind.startswith("write"))
    near=Counter(owner for owner,kind in mapped
                 if kind.startswith("write") and RELEVANT_LO<=owner<RELEVANT_HI)
    stats=dict(sections=sections,loads=typecount["load"],
               word_writes=typecount["write_word"],
               byte_writes=typecount["write_byte"],
               half_writes=typecount["write_half"],
               owner_writers=len(writes),near_writer_owners=len(near),
               unmapped=sum(owner==0 for owner,_ in mapped))
    return stats,near


def audit(data:bytes)->list[str]:
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("digest")
    functions=parse_functions(data)
    if len(functions)<25000:raise ValueError("symbols")
    inputs=[]
    for owner in SC_WRITERS:
        size=functions.get(owner,0)
        if size<32 or size>32768 or size%4:raise ValueError("function_bounds")
        edges=input_edges(owner,read_words(data,owner,size//4))
        if len(edges)!=2:raise ValueError("input_edges")
        inputs.extend((owner,*edge) for edge in edges)
    stats,candidates=scan_executable(data,functions)
    rows=[
        "V275_SC_FIELD links=4 "+
        " ".join(f"{k}={v}" for k,v in stats.items())
    ]
    for owner,store,load,ra,rt in inputs:
        rows.append(
            f"V275_FIELD_INPUT owner={owner:08x} store_offset={store} "
            f"load_offset={load} base_reg={ra} value_reg={rt}")
    for rank,(owner,count) in enumerate(sorted(
        candidates.items(),key=lambda v:(-v[1],v[0]))[:12],1):
        rows.append(
            f"V275_FIELD_WRITER rank={rank} owner={owner:08x} stores={count}")
    return rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_owner_elf",type=Path)
    args=p.parse_args()
    try: lines=audit(args.private_owner_elf.read_bytes())
    except (OSError,ValueError):
        print("V275_FIELD_AUDIT verified=0",file=sys.stderr)
        return 1
    print("V275_FIELD_AUDIT verified=1")
    print("\n".join(lines))
    return 0

if __name__=="__main__":
    sys.exit(main())
