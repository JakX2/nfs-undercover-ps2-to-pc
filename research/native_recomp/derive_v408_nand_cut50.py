#!/usr/bin/env python3
"""V408: independent original Wii AOT exact 50-call native cutpoint.

V406 authenticated original guest call entries 49 and 50 before the
V404/V405 96-call candidate aborted with a public host assertion. This
read-only derivative of V404's separate private harness shortens only
the observer stop to call 50, testing whether it can stop cleanly at
that boundary. It never alters generated PPC code, CPU registers,
IOS/NAND, previous 24/48/96-call processes or guest call targets.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

CAP_SEAMS={
    'if(owned||v396_calls==96u){':('if(owned||v396_calls==50u){',1),
    'const bool bounded=!owned&&v396_calls==96u;':(
        'const bool bounded=!owned&&v396_calls==50u;',1),
    'nwii::runtime::v396_calls==96u':('nwii::runtime::v396_calls==50u',2),
    'nwii::runtime::v396_calls<=96u':('nwii::runtime::v396_calls<=50u',2),
}
MARKERS={
    'V404_NAND_EXTENDED_STOP calls=':'V408_NAND_CUT50_STOP calls=',
    'V404_NAND_EXTENDED_TRIAL calls=':'V408_NAND_CUT50_TRIAL calls=',
}
LABEL_OLD='v404_completed'
LABEL_NEW='v408_completed'
def patch(source:str)->str:
    if (any(source.count(m)!=1 for m in MARKERS) or
        source.count(LABEL_OLD)!=3 or
        'V408_NAND_CUT50_STOP calls=' in source or
        source.count('V403_NAND_CALL_PROVENANCE ctr=')!=1 or
        source.count('V401_NAND_CALLSITE mapped=')!=1 or
        source.count('V370_NAND_FLAG_W1C n=')!=1 or
        not 1<=source.count('try{run_game(c);}')<=16):
        raise ValueError('geometry')
    out=source
    for i,(old,(new,expected)) in enumerate(CAP_SEAMS.items(),1):
        if out.count(old)!=expected:
            raise ValueError(f'cap_{i}')
        out=out.replace(old,new)
    for old,new in MARKERS.items():
        out=out.replace(old,new,1)
    out=out.replace(LABEL_OLD,LABEL_NEW)
    if (out.count('if(owned||v396_calls==50u){')!=1 or
        out.count('const bool bounded=!owned&&v396_calls==50u;')!=1 or
        out.count('nwii::runtime::v396_calls==50u')!=2 or
        out.count('nwii::runtime::v396_calls<=50u')!=2 or
        out.count(LABEL_NEW)!=3 or
        any(out.count(m)!=1 for m in MARKERS.values()) or
        out.count('try{run_game(c);}')!=source.count('try{run_game(c);}') or
        out.count('V403_NAND_CALL_PROVENANCE ctr=')!=1 or
        out.count('V401_NAND_CALLSITE mapped=')!=1 or
        out.count('V370_NAND_FLAG_W1C n=')!=1):
        raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_private_96_call_harness',type=Path)
    p.add_argument('next_private_50_call_harness',type=Path)
    a=p.parse_args()
    try:
        if a.next_private_50_call_harness.exists() or a.next_private_50_call_harness.is_symlink():
            raise ValueError('output_exists')
        with a.next_private_50_call_harness.open('x',encoding='utf-8') as f:
            f.write(patch(a.prior_private_96_call_harness.read_text(encoding='utf-8')))
    except (OSError,ValueError) as exc:
        reason=str(exc) if isinstance(exc,ValueError) else 'io'
        if reason not in {'geometry','cap_1','cap_2','cap_3','cap_4','route','output_exists','io'}:
            reason='other'
        print(f'V408_NAND_CUT50_ERROR reason={reason}',file=sys.stderr)
        print('V408_NAND_CUT50_ROUTE installed=0',file=sys.stderr)
        return 1
    print('V408_NAND_CUT50_ROUTE installed=1 original_guest=1 cap50=1 baseline48_preserved=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
