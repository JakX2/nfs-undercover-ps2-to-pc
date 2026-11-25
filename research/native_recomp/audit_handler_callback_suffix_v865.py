#!/usr/bin/env python3
"""Private geometry after either authenticated original SI callback return."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import geometry,HANDLER
from prepare_v667_si_dispatch import exact
from prepare_v789_alarm_suffix import expectations
from audit_callback_frontiers_v799 import call_sites
from audit_handler_suffix_v728 import suffix,classify_target
from make_private_elf_symbol_map import parse_functions

def inspect(dol,elf):
    n,*_=geometry(dol,elf)
    words=exact(dol,elf,HANDLER,n)
    _,_,sites=expectations(dol,elf)
    calls=call_sites(HANDLER,words)
    if len(sites)!=2 or any(calls[o-1]!=(pc,2,None) for o,pc in zip((6,11),sites)):
        raise ValueError('callback sites')
    sizes=parse_functions(elf)
    for o,pc in zip((6,11),sites):
        labels,backs,stores,stops=suffix(HANDLER,words,pc+4)
        if not labels or not stops:raise ValueError('handler continuation')
        print(f'V865_HANDLER_SUFFIX after={o} labels={labels} backward={backs} stores={stores} boundaries={len(stops)} execution=0')
        for i,(_,kind,ordinal,dst) in enumerate(stops,1):
            root,owners,restore,symbol=classify_target(dol,elf,dst,sizes)
            print(f'V865_HANDLER_BOUNDARY after={o} boundary={i} kind={kind} ordinal={ordinal} exact_root={root} containing={owners} restore_gprs={restore} alias_symbol={symbol}')
    print('V865_HANDLER_CENSUS verified=1 callback_sites=2 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError,IndexError,KeyError):
        print('V865_HANDLER_CENSUS verified=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
