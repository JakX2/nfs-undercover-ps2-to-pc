#!/usr/bin/env python3
"""Authenticate private boot-report computed branch geometry, without exporting bytes."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,words_at,direct_bl
from prepare_v453_debug_leaf import data_at
from audit_v264_osinit_retry_elf import read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from make_start_to_boot_report_v66 import DATA,EDGES,RANGES,STOP
START=0x805203c4;END=0x80520670;TABLE=0x8060b7a8+496
TARGETS=tuple(range(0x805204ec,0x8052054c+1,16))
REPORT=0x80522f00
def check_table(raw):
    if len(raw)!=104:raise ValueError('table size')
    entries=struct.unpack('>26I',raw)
    if set(entries)!=set(TARGETS):raise ValueError('table targets')
    return entries
def check_control(words):
    if len(words)!=(END-START)//4 or words[-1]!=0x4e800020:raise ValueError('report extent')
    bctr=[START+4*i for i,w in enumerate(words) if w==0x4e800420]
    if len(bctr)!=1 or not START<=bctr[0]<TARGETS[0]:raise ValueError('computed branch')
    idx=(bctr[0]-START)//4
    prior=words[max(0,idx-12):idx]
    ctr=[w for w in prior if w>>26==31 and ((w>>1)&1023)==467 and (((w>>16)&31)|(((w>>11)&31)<<5))==9]
    if len(ctr)!=1:raise ValueError('CTR definition')
    for dest in TARGETS[:-1]:
        site=dest+8
        if direct_bl(words[(site-START)//4],site)!=REPORT:raise ValueError('console case call')
    return bctr[0]
def geometry(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    if hashlib.sha256(dol).hexdigest()!=dd or hashlib.sha256(elf).hexdigest()!=ed:raise ValueError('identity')
    funcs=parse_functions(elf)
    if funcs.get(START)!=END-START or any(START<pc<END for pc in funcs):raise ValueError('ELF extent')
    for lo,hi in RANGES:
        code=words_at(dol,lo,(hi-lo)//4)
        if tuple(read_words(elf,lo,len(code)))!=code or code[-1]!=0x4e800020:raise ValueError('original code identity')
    for site,dest in EDGES:
        w=words_at(dol,site,1)
        if tuple(read_words(elf,site,1))!=w or direct_bl(w[0],site)!=dest:raise ValueError('call edge')
    table=check_table(data_at(dol,TABLE,104))
    report=data_at(dol,*DATA[0]);small=data_at(dol,*DATA[1])
    if struct.unpack_from('>I',small)[0]!=DATA[0][0]:raise ValueError('version pointer')
    for off in (72,88,112,124,136,152,244,256,268,280,292,304,328,384,412,424,440,468):
        if not report[off] or b'\0' not in report[off:496]:raise ValueError('format geometry')
    return check_control(words_at(dol,START,(END-START)//4)),table
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        geometry(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error):
        print('V594_REPORT_GEOMETRY owner=1 accepted=0');return 1
    print('V594_REPORT_GEOMETRY owner=1 accepted=1 table=26 targets=7 root=1 original_edges=10')
    return 0
if __name__=='__main__':raise SystemExit(main())
