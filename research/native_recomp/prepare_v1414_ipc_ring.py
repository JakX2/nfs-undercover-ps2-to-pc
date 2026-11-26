#!/usr/bin/env python3
"""Identify a private writable IPC ring object without exporting symbol data."""
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL
import struct

def ring_object(dol,elf):
    if len(elf)<HEADER.size or len(dol)<256:raise ValueError('ring image')
    h=HEADER.unpack_from(elf);off,unit,n=h[6],h[11],h[12]
    if h[0][:7]!=b'\x7fELF\x01\x02\x01' or h[2]!=20 or unit!=SECTION.size or not 1<=n<10000 or off+n*unit>len(elf):
        raise ValueError('ring ELF sections')
    rows=[SECTION.unpack_from(elf,off+i*unit) for i in range(n)]
    found=set()
    for _,kind,_,_,at,size,link,_,_,entsize in rows:
        if kind!=2:continue
        if entsize!=SYMBOL.size or size%entsize or size>16*1024*1024 or at+size>len(elf) or not 0<link<len(rows):
            raise ValueError('ring symbol table')
        _,sk,_,_,sa,sn,*_=rows[link]
        if sk!=3 or sa+sn>len(elf) or sn>32*1024*1024:raise ValueError('ring strings')
        strings=elf[sa:sa+sn]
        for pos in range(at,at+size,entsize):
            name,addr,length,info,_,ndx=SYMBOL.unpack_from(elf,pos)
            if name>=len(strings) or not strings.startswith(b'__responses\x00',name):continue
            if (info&15)!=1 or not 0<ndx<len(rows):raise ValueError('ring object type')
            sec=rows[ndx]
            if sec[1] not in (1,8) or sec[2]&7!=3 or addr&3 or not 24<=length<=272 or (length-16)%4:
                raise ValueError('ring object shape')
            if not sec[3]<=addr<addr+length<=sec[3]+sec[5] or not 0x80004000<=addr<addr+length<=0x81800000:
                raise ValueError('ring object range')
            found.add((addr,length))
    if len(found)!=1:raise ValueError('ring object identity')
    addr,length=next(iter(found))
    def u32(at):return struct.unpack_from('>I',dol,at)[0]
    def contains(base,size):return base<=addr and addr+length<=base+size
    def overlap(base,size):return size and base<addr+length and addr<base+size
    if any(overlap(u32(0x48+4*i),u32(0x90+4*i)) for i in range(7)):
        raise ValueError('ring text overlap')
    in_data=any(contains(u32(0x64+4*i),u32(0xac+4*i)) for i in range(11))
    if not in_data and not contains(u32(0xd8),u32(0xdc)):raise ValueError('ring DOL range')
    return addr,length,(length-16)//4

def ring_sites(words,owner,first,stop):
    sites=tuple(pc for pc,(a,w) in sorted(words.items()) if a==owner and w>>26==36 and (w>>16)&31 not in (0,1,2,13))
    if len(sites)!=3 or sites[0]!=first or any(not first<=pc<stop for pc in sites):
        raise ValueError('ring store sites')
    return sites
