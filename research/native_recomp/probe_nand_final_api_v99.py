#!/usr/bin/env python3
"""Private owner-local metadata at the FS/next IOS wrapper continuation.

No executable bytes, private symbol names, private resource literals or file
contents leave the runner. Only allowlisted public SDK API identities and
bounded direct dependency geometry are reported.
"""
import argparse,hashlib,struct
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA,get_text
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions,HEADER,SECTION,SYMBOL
from probe_post_v68 import describe,MAX_SIZE
from probe_next_osinit_v33 import classify

ROOTS=(0x8051e5bc,0x8054b114,0x8054a414,0x8051f634,0x8051f5e0,0x8054af38,
       0x804f1e2c,0x8051982c,0x80519094,0x8051e5b8)
PUBLIC=("ISFS_Initialize","ISFS_Deinitialize","ISFS_GetAttr","ISFS_GetUsage",
        "ISFS_GetStats","ISFS_ReadDir","NANDInit","NANDInitAsync","NANDPrivateGetType",
        "ES_Init","ES_Close","ES_GetTitleID","ES_GetTitleId","ES_GetDataDir","ES_GetTitleDir",
        "ES_Initialize","ES_Deinitialize","IOS_Open","IOS_Close","IOS_Ioctl","IOS_Ioctlv",
        "IOS_CreateHeap","IPCInit","IPCCltInit","DVDInit","DVDLowInit","OSGetConsoleType",
        "IOS_IoctlAsync","IOS_IoctlvAsync","IOS_OpenAsync","IOS_CloseAsync",
        "ISFS_CreateDir","ISFS_CreateFile","ISFS_GetFileStats","ISFS_GetAttrAsync","ISFS_CreateDirAsync",
        "NANDCreateDir","NANDCreateDirAsync","NANDPrivateCreateDir","NANDPrivateCreateDirAsync",
        "sprintf","snprintf","vsprintf","vsnprintf","__pformatter","__StringWrite","__StringRead")

def public_matches(elf):
    head=HEADER.unpack_from(elf)
    shoff,shentsize,shnum=head[6],head[11],head[12]
    if shentsize!=SECTION.size or not 0<shnum<10000 or shoff+shnum*shentsize>len(elf):
        raise ValueError("invalid owner section geometry")
    sections=[SECTION.unpack_from(elf,shoff+i*shentsize) for i in range(shnum)]
    matches=set()
    for sec in sections:
        _,kind,_,_,off,size,link,_,_,entsize=sec
        if kind!=2:continue
        if link>=len(sections) or entsize!=SYMBOL.size or off+size>len(elf):
            raise ValueError("invalid owner symbol geometry")
        strings=sections[link]
        start,end=strings[4],strings[4]+strings[5]
        if strings[1]!=3 or end>len(elf):raise ValueError("invalid owner string section")
        for at in range(off,off+size,entsize):
            name,addr,_,info,_,_=SYMBOL.unpack_from(elf,at)
            if addr not in ROOTS or info&15!=2 or start+name>=end:continue
            stop=elf.find(b"\0",start+name,min(end,start+name+64))
            if stop<0:continue
            for i,api in enumerate(PUBLIC):
                if elf[start+name:stop]==api.encode("ascii"):matches.add((addr,i))
    return sorted(matches)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("dol",type=Path);p.add_argument("elf",type=Path)
    a=p.parse_args()
    dol=a.dol.read_bytes();elf=a.elf.read_bytes()
    if hashlib.sha256(dol).hexdigest()!=ORIGINAL_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError("owner digest mismatch")
    funcs=parse_functions(elf)
    for addr,i in public_matches(elf):
        print(f"V99_PUBLIC_API addr=0x{addr:08X} api={PUBLIC[i]}")
    for addr in ROOTS:
        if not 0<funcs.get(addr,0)<=0x1000:raise ValueError("missing bounded function")
        code=get_text(dol,addr,funcs[addr])
        _,edges=classify(code,addr)
        if len(edges)>24:
            # Large CRT helper is identified by public API name only.
            # Do not emit a broad dependency inventory.
            continue
        calls=describe(dol,funcs,addr)
        # Inspect only the direct IOS request wrapper call's immediate
        # public selector/count arguments. Do not emit arbitrary constants.
        for site,dest in calls:
            if dest!=0x8051982c:continue
            for reg in (4,5,6):
                value=None
                for pc in range(site-4,max(addr-4,site-40),-4):
                    word=struct.unpack_from(">I",code,pc-addr)[0]
                    if (word>>26)==14 and ((word>>21)&31)==reg and ((word>>16)&31)==0:
                        value=word&0xffff;break
                if value is not None and value<=0x40:
                    print(f"V99_REQUEST_ARG site=0x{site:08X} register={reg} value={value}")
    print("PASS: bounded authenticated V99 final NAND API metadata")
if __name__=="__main__":main()
