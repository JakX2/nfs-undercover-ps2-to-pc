#!/usr/bin/env python3
"""Classify a refused nested data read, without supplying a guessed value."""
import argparse,struct
from pathlib import Path
from analyze_formatter_nested_path import plan as nested_plan
from make_private_elf_symbol_map import HEADER,SECTION
from make_v1243_stm_fixture import data_at,seed_data
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from prepare_post_stm_sc_state import overlap,store_kind
from prepare_post_stm_sc_version import elf_data
from prepare_v629_stm_open import geometry
from prepare_v1385_async_ioctl_geometry import plan as ioctl_plan
from prepare_v1337_open_completion import plan as completion

def classify_section(elf,addr,n):
    h=HEADER.unpack_from(elf);off,unit,count=h[6],h[11],h[12]
    if h[0][:7]!=b'\x7fELF\x01\x02\x01' or h[2]!=20 or unit!=SECTION.size or not 1<=count<10000 or off+count*unit>len(elf):
        raise ValueError('nested audit sections')
    hits=[SECTION.unpack_from(elf,off+i*unit) for i in range(count)]
    hits=[x for x in hits if x[2]&2 and overlap(addr,n,x[3],x[5])]
    if len(hits)!=1:return 'ambiguous'
    _,kind,flags,base,fo,size,*_=hits[0]
    if not base<=addr<addr+n<=base+size:return 'partial'
    if flags&4:return 'executable'
    if kind==8:return 'bss'
    if kind!=1 or fo+size>len(elf):return 'other'
    return 'writable' if flags&1 else 'readonly'

def direct_writers(words,addr,n):
    direct=0
    for w in words:
        width=store_kind(w);ra=(w>>16)&31
        if width<=0 or ra not in (2,13):continue
        disp=((w&0xffff)^0x8000)-0x8000
        if overlap(addr,n,(EXPECTED_GPRS[ra]+disp)&0xffffffff,width):direct+=1
    return direct

def plan(d,e):
    missed=[]
    try:nested_plan(d,e,on_unknown=lambda a,n:missed.append((a,n)))
    except ValueError:
        if len(missed)!=1:raise ValueError('nested audit refusal')
    else:raise ValueError('nested audit no refusal')
    addr,n=missed[0]
    kind=classify_section(e,addr,n)
    data=data_at(d,addr,n)
    equal=False
    if data is not None and kind in ('writable','readonly'):
        try:equal=elf_data(e,addr,n)==data
        except ValueError:pass
    _,stm,_,_,paths,_=geometry(d,e)
    roots=ioctl_plan(d,e)[0];shared=completion(d,e)[0]
    seeded=seed_data(d,tuple(stm)+tuple(w for words in roots.values() for w in words),paths)
    covered=sum(addr+i in seeded for i in range(n))
    matches=sum(addr+i in seeded and data is not None and seeded[addr+i]==data[i] for i in range(n))
    writers=direct_writers(tuple(stm)+tuple(w for words in (*roots.values(),*shared.values()) for w in words),addr,n)
    return kind,n,int(data is not None),int(equal),covered,matches,writers

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','nested audit sections','nested audit refusal','nested audit no refusal'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        kind,n,mapped,equal,covered,matches,writers=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_NESTED_READ_AUDIT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'FORMATTER_NESTED_READ_AUDIT verified=1 section={kind} width={n} dol_initialized={mapped} elf_agreement={equal} inherited_seed_bytes={covered} matching_seed_bytes={matches} earlier_direct_writers={writers} live_value_verified=0 original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
