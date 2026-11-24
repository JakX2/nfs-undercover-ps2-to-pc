#!/usr/bin/env python3
"""Scope only V260's obsolete discovery stop in a separate 96-call candidate."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from derive_v411_nand_host_stop import TOKENS

FRONTIER='    if(v260_post_calls==64u){'
MARKER='V260_CALL_FRONTIER guest='
STOP='ctx.is_running=false;throw ExceptionStop{};'
RESUME='''if(v250_candidate_mode&&v250_nand_seen==1u&&v388_active&&
         v389_after_y1&&v389_flag_seen==1u&&v395_next_seen==1u&&
         v396_calls>=50u&&v396_calls<96u){
        std::cout<<"V412_LEGACY_FRONTIER continued=1"<<std::endl;
      }else{
        ctx.is_running=false;throw ExceptionStop{};
      }'''

def patch(source:str)->str:
    # Use exactly the V411 lexical census, not a guessed ordinal. Require
    # the original public V260 witness, its cap, and its final stop.
    anchors=(FRONTIER,MARKER,'V410_NAND_GUEST_RUN_EXIT calls=',
             'V405_NAND_SECOND_HALF tail_calls=',
             'V260 post-IPC original guest bounded call context invalid',
             'if(owned||v396_calls==96u){')
    if any(source.count(a)!=1 for a in anchors) or 'V412_LEGACY_FRONTIER' in source:
        raise ValueError('geometry')
    begin=source.index(FRONTIER)
    mark=source.index(MARKER)
    end=source.find('\n    }\n  }',mark)
    if not begin<mark<end<begin+10000:
        raise ValueError('geometry')
    block=source[begin:end]
    if (block.count(STOP)!=1 or not block.rstrip().endswith(STOP) or
        any(a not in block for a in ('++v260_frontier_seen;',
                                    'v260_frontier_pc=addr;',
                                    'v260_frontier_lr=ctx.lr;'))):
        raise ValueError('geometry')
    at=begin+block.index(STOP)
    sites=[m for m in TOKENS.finditer(source) if m.group('assignment') is not None]
    matches=[i for i,m in enumerate(sites,1) if m.start()==at+len('ctx.')]
    if len(sites)!=19 or matches!=[12]:
        raise ValueError('site_mismatch')
    if not re.match(r'\s*;\s*throw\s+ExceptionStop\s*\{\s*\}',source[sites[11].end():]):
        raise ValueError('site_mismatch')
    # Retain the V260 witness, cap, ABI check and observer bookkeeping.
    # v260_frontier_seen=1 makes that one-shot observer retire naturally.
    out=source[:at]+RESUME+source[at+len(STOP):]
    if out.count(RESUME)!=1 or out.replace(RESUME,STOP,1)!=source:
        raise ValueError('route')
    return out

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    try:
        out=patch(a.prior.read_text(encoding='utf-8'))
        with a.output.open('x',encoding='utf-8') as f:f.write(out)
    except (OSError,ValueError) as e:
        reason=str(e) if isinstance(e,ValueError) else 'io'
        if reason not in ('geometry','site_mismatch','route','io'):reason='other'
        print(f'V412_LEGACY_ROUTE installed=0 reason={reason}')
        return 1
    print('V412_LEGACY_ROUTE installed=1 site=12 legacy_v260=1 guards_preserved=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
