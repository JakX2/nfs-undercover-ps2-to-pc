#!/usr/bin/env python3
"""V404: independent native original-Wii NAND/ISFS successor horizon, 96 calls.

Transform ONLY the private V402 48-call candidate into a second native
candidate, never the independently verified 24-call V403 or 48-call V402
process. Preserve all original translated PowerPC, IOS, NAND, PC, LR, CTR,
SP and memory state; change only the bounded observer stop and predicates.
No successful boot claim.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

CAP_SEAMS={
    'if(owned||v396_calls==48u){': ('if(owned||v396_calls==96u){',1),
    'const bool bounded=!owned&&v396_calls==48u;':
        ('const bool bounded=!owned&&v396_calls==96u;',1),
    'nwii::runtime::v396_calls==48u':
        ('nwii::runtime::v396_calls==96u',2),
    'nwii::runtime::v396_calls<=48u':
        ('nwii::runtime::v396_calls<=96u',2),
}
MARKERS={
    'V402_NAND_LONG_STOP calls=': 'V404_NAND_EXTENDED_STOP calls=',
    'V402_NAND_LONG_TRIAL calls=': 'V404_NAND_EXTENDED_TRIAL calls=',
}
LABEL='v402_completed'
OUTPUT='v404_completed'

def patch(source:str)->str:
    if (any(source.count(old)!=1 for old in MARKERS) or
        source.count(LABEL)!=3 or
        source.count('V401_NAND_CALLSITE mapped=')!=1 or
        source.count('V403_NAND_CALL_PROVENANCE mapped=')!=0 or
        source.count('V403_NAND_CALL_PROVENANCE ctr=')!=1 or
        source.count('V370_NAND_FLAG_W1C n=')!=1 or
        not (1<=source.count('try{run_game(c);}')<=16) or
        'V404_NAND_EXTENDED_STOP calls=' in source):
        raise ValueError('geometry')
    out=source
    for i,(old,(new,expected)) in enumerate(CAP_SEAMS.items(),1):
        if out.count(old)!=expected:
            raise ValueError(f'cap_{i}')
        out=out.replace(old,new)
    for old,new in MARKERS.items():
        out=out.replace(old,new,1)
    out=out.replace(LABEL,OUTPUT)
    if (out.count('if(owned||v396_calls==96u){')!=1 or
        out.count('const bool bounded=!owned&&v396_calls==96u;')!=1 or
        out.count('nwii::runtime::v396_calls==96u')!=2 or
        out.count('nwii::runtime::v396_calls<=96u')!=2 or
        out.count(OUTPUT)!=3 or
        any(out.count(new)!=1 for new in MARKERS.values()) or
        out.count('try{run_game(c);}')!=source.count('try{run_game(c);}') or
        out.count('V401_NAND_CALLSITE mapped=')!=1 or
        out.count('V403_NAND_CALL_PROVENANCE ctr=')!=1 or
        out.count('V370_NAND_FLAG_W1C n=')!=1):
        raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_48_call_harness',type=Path)
    p.add_argument('next_private_96_call_harness',type=Path)
    args=p.parse_args()
    try:
        if args.next_private_96_call_harness.exists() or args.next_private_96_call_harness.is_symlink():
            raise ValueError('output_exists')
        with args.next_private_96_call_harness.open('x',encoding='utf-8') as f:
            f.write(patch(args.prior_private_48_call_harness.read_text(encoding='utf-8')))
    except (ValueError,OSError) as exc:
        reason=str(exc) if isinstance(exc,ValueError) else 'io'
        if reason not in {'geometry','cap_1','cap_2','cap_3','cap_4',
                          'route','output_exists','io'}:
            reason='other'
        print(f'V404_NAND_EXTENDED_ERROR reason={reason}',file=sys.stderr)
        print('V404_NAND_EXTENDED_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V404_NAND_EXTENDED_ROUTE installed=1 original_guest=1 cap=96 baseline48_preserved=1')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
