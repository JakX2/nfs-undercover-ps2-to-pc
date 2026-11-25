#!/usr/bin/env python3
"""Count geometry only. Never disclose a private instruction, address or symbol."""
import argparse,struct
from pathlib import Path
from prepare_v668_si_ack import geometry,shape,HANDLER,is_word_store
from prepare_v419_full_start import MAX_DOL,words_at
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from apply_si_roots_v669 import ROOTS,spans,pairs
from si_helper_geometry_v680 import helper_geometry
from classify_save_leaf_v683 import symbol_evidence,inspect_suffix
def classify(dol,elf):
    n,_,_,_,_=geometry(dol,elf)
    handler=words_at(dol,HANDLER,n);_,direct,indirect=shape(HANDLER,handler)
    if not direct:raise ValueError('missing direct')
    site,target=direct[0];sizes=parse_functions(elf);size=sizes.get(target,0)
    owners=[(a,s) for a,s in sizes.items() if a<target<a+s]
    result=dict(first_direct=int(not indirect or site<min(indirect)),exact_root=int(bool(size)),
                containing=len(owners),bounded=int(4<=size<=4096 and not size&3),
                base_root=int(target in ROOTS),returns=0,conditional_returns=0,stores=0,nested=0,external_tails=0,
                identity=0,overlap=0,admissible=0)
    if size and 4<=size<=4096 and not size&3:
        words=exact(dol,elf,target,size//4);result['identity']=1
        for i,w in enumerate(words):
            op=w>>26;xo=(w>>1)&1023
            result['returns']+=w==0x4e800020
            result['conditional_returns']+=op==19 and xo==16 and not w&1 and w!=0x4e800020
            result['stores']+=is_word_store(w)
            result['nested']+=bool(w&1) and (op in (16,18) or op==19 and xo in (16,528))
            if op in (16,18) and not w&1:
                bits,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
                disp=((w&bits)^sign)-sign
                dst=(disp if w&2 else target+4*i+disp)&0xffffffff
                result['external_tails']+=not target<=dst<target+size
        result['overlap']=sum(a!=target and a<target+size and target<a+s for a,s in spans(dol,elf))
    result.update(symbol_evidence(elf,target))
    result.update(save_kind=0,save_registers=0)
    try:
        leaf=inspect_suffix(dol,elf,target)
        result.update(save_kind=leaf['kind'],save_registers=leaf['registers'])
    except ValueError:pass
    try:helper_geometry(dol,elf);pairs(spans(dol,elf,True));result['admissible']=1
    except ValueError:pass
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        r=classify(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V682_SI_FIRST_HELPER inspected=0');return 1
    print('V682_SI_FIRST_HELPER inspected=1 '+' '.join(f'{k}={v}' for k,v in r.items()))
    return 0
if __name__=='__main__':raise SystemExit(main())
