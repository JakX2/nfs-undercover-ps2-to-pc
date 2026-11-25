#!/usr/bin/env python3
"""Private same-thread dispatcher epilogue/context-loader geometry census."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from make_start_to_irq_dispatch_v76 import EDGES,DISPATCH
from audit_si_deep_v695 import call_kind
def inspect(dol,elf):
    sizes=parse_functions(elf);out=[]
    dispatch=exact(dol,elf,DISPATCH,0x2a4//4)
    after=[(pc,dst) for pc,dst in EDGES if pc>=0x80526cac]
    for pc,dst in after:
        if direct_bl(dispatch[(pc-DISPATCH)//4],pc)!=dst:raise ValueError('return edge')
    for kind,root in enumerate((0x80529434,0x80529940,0x805229b4),1):
        n=sizes.get(root,0)
        if not 0<n<=4096 or n%4:raise ValueError('return extent')
        code=exact(dol,elf,root,n//4)
        row=dict(kind=kind,words=len(code),direct=sum(call_kind(w)==1 for w in code),
                 indirect=sum(call_kind(w)==2 for w in code),blr=code.count(0x4e800020),
                 rfi=code.count(0x4c000064),mtmsr=sum(w>>26==31 and (w>>1)&1023==146 for w in code))
        out.append(row)
    return len(after),out
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        n,rows=inspect(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V706_RETURN_GEOMETRY verified=0');return 1
    print(f'V706_RETURN_GEOMETRY verified=1 edges={n} roots={len(rows)} execution=0')
    for row in rows:print('V706_RETURN_ROOT '+' '.join(f'{k}={v}' for k,v in row.items()))
    return 0
if __name__=='__main__':raise SystemExit(main())
