#!/usr/bin/env python3
"""Private read-only STM post-Open control/data census, with no guest execution."""
import argparse,struct
from pathlib import Path
from prepare_v629_stm_open import geometry,STM
from make_start_to_stm_v70 import STM_SIZE,EDGES,IOCTL
from prepare_v1337_open_completion import SECOND
from make_v1243_stm_fixture import seed_data
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def scan(root,words,start,allowed):
    end=root+4*len(words)
    if not root<=start<end or (root|start)&3 or not words:
        raise ValueError('tail extent')
    work=[start];seen=set();calls=set();returns=set();stores=set();sda=set()
    def target(pc,w):
        m,s=(0xfffc,0x8000) if w>>26==16 else (0x03fffffc,0x02000000)
        return (pc+((w&m)^s)-s)&0xffffffff
    while work:
        pc=work.pop()
        if pc in seen:continue
        if not root<=pc<end or pc&3:raise ValueError('tail escape')
        seen.add(pc)
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023;ra=(w>>16)&31
        if op==18 and w&1:
            dst=direct_bl(w,pc)
            if dst is None or allowed.get(pc)!=dst:raise ValueError('tail call')
            calls.add((pc,dst));work.append(pc+4);continue
        if w==0x4e800020:
            returns.add(pc);continue
        if op==17 or (op==19 and xo in (16,50,528)) or (op==31 and xo==146):
            raise ValueError('tail control')
        if op in (16,18):
            if w&3:raise ValueError('tail control')
            work.append(target(pc,w))
            if op==16 and (w>>21)&20!=20:work.append(pc+4)
            continue
        if op in (36,37,38,39,44,45,47,52,53,54,55):stores.add(pc)
        if op in (32,34,40,36,38,44) and ra in (2,13):sda.add(pc)
        work.append(pc+4)
    if not returns or calls!=set(allowed.items()):raise ValueError('tail reachability')
    return seen,calls,returns,stores,sda

def audit(dol,elf):
    _,body,_,_,paths,_=geometry(dol,elf)
    if len(body)*4!=STM_SIZE:raise ValueError('tail extent')
    start=SECOND+4
    allowed={pc:dst for pc,dst in EDGES if pc>=start}
    if len(allowed)!=3 or sum(dst==IOCTL for dst in allowed.values())!=1:raise ValueError('tail call')
    seen,calls,returns,stores,sda=scan(STM,body,start,allowed)
    # Seed only initialized original data privately. No public addresses,
    # bytes, words, register operands, or generated code in the report.
    old=seed_data(dol,body[:(start-STM)//4],paths)
    full=seed_data(dol,body,paths)
    if any(full.get(a)!=v for a,v in old.items()):raise ValueError('tail seed identity')
    size=parse_functions(elf).get(IOCTL,0)
    if not 4<=size<=4096 or size%4:raise ValueError('ioctl extent')
    ioctl=exact_words(dol,elf,IOCTL,size//4)
    ioctl_calls=sum(w>>26==18 and w&3==1 for w in ioctl)
    print(f'V1377_STM_TAIL verified=1 total_words={len(body)} reachable_after_second={len(seen)} '
          f'direct_calls={len(calls)} returns={len(returns)} direct_store_sites={len(stores)} '
          f'sda_sites={len(sda)} additional_seed_bytes={len(full)-len(old)} '
          f'ioctl_words={len(ioctl)} ioctl_direct_calls={ioctl_calls} original_execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        audit(a.dol.read_bytes(),a.elf.read_bytes())
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as e:
        allowed={'tail extent','tail escape','tail call','tail control','tail reachability','tail seed identity','ioctl extent','size'}
        print('V1377_STM_TAIL verified=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'private_input_or_io'))
        return 1
if __name__=='__main__':raise SystemExit(main())
