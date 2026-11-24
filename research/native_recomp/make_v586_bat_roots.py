#!/usr/bin/env python3
"""Private, exact DOL/ELF matching for the three physical BAT mapping roots."""
import argparse,hashlib,struct
from pathlib import Path
from audit_v584_bat_translation import MAPS,geometry
from audit_v264_osinit_retry_elf import read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions,csv_lines
from prepare_v419_full_start import OWNER_SHA,words_at,direct_bl
CALLS=((0x805275cc,0x80527550),(0x805275fc,0x80527550))
def plan(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    geometry(dol,dd)
    if hashlib.sha256(elf).hexdigest()!=ed:raise ValueError('ELF identity')
    funcs=dict(parse_functions(elf))
    if len(funcs)<25000:raise ValueError('ELF map')
    for pc,target in CALLS:
        w=words_at(dol,pc,1)
        if tuple(read_words(elf,pc,1))!=w or direct_bl(w[0],pc)!=target:raise ValueError('trampoline caller')
    roots=covered=missing=0
    original=dict(funcs)
    for lo,hi,_ in MAPS:
        n=(hi-lo)//4
        if tuple(read_words(elf,lo,n))!=words_at(dol,lo,n):raise ValueError('DOL ELF mismatch')
        roots+=int(lo in original)
        covered+=sum(any(a<=pc and pc+4<=a+size for a,size in original.items()) for pc in range(lo,hi,4))
        missing+=int(lo not in original)
        # No arbitrary symbol expansion. Only these authenticated straight-line
        # regions may be added; retain any preexisting larger extent unchanged.
        funcs[lo]=max(funcs.get(lo,0),hi-lo)
    return funcs,(roots,covered,missing)
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('csv',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024 or a.csv.exists() or a.csv.is_symlink():raise ValueError('input')
        funcs,(roots,covered,missing)=plan(a.dol.read_bytes(),a.elf.read_bytes())
        with a.csv.open('x',encoding='utf-8') as f:f.write(csv_lines(funcs))
    except (OSError,ValueError,struct.error):print('V586_BAT_ROOTS accepted=0');return 1
    print(f'V586_BAT_ROOTS accepted=1 original_roots={roots} covered_words={covered} added_roots={missing} exact_dol_elf=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
