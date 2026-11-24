#!/usr/bin/env python3
"""Locate the host run-stop assignment after original guest call 49.

Instrument only the private V405 harness (independently authored host code).
Do not change a stop value, exception, guest register, translated PPC, or
the historical V390 acceptance predicate. Site IDs are source ordinals;
the private generated harness and arbitrary source text are never printed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

# Match C++ comments and literals before matching executable assignments.
# Raw strings use their own captured delimiter; ordinary strings/chars
# allow escaped characters. Preserve the whole matched prefix verbatim.
TOKENS=re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|(?:u8|u|U|L)?R"(?P<delim>[^ ()\\\t\r\n]{0,16})\([\s\S]*?\)(?P=delim)"'
    r'|"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\''
    r'|(?P<assignment>\bis_running\s*=\s*)(?P<value>false)\b'
)
ARM='    if(v396_calls>48u&&v396_calls<=96u){'
RESET='  nwii::runtime::v405_tail_calls=0u;'
HEADER=r'''#include <cstdio>
// Independent host-only diagnostic state; no guest mutation.
static bool v411_stop_armed=false;
static unsigned v411_stop_events=0u;
static bool v411_note_host_stop(unsigned site,unsigned throws){
    if(v411_stop_armed&&v411_stop_events<8u){
        ++v411_stop_events;
        std::fprintf(stderr,"V411_HOST_STOP event=%u site=%u throws=%u\n",
                     v411_stop_events,site,throws);
        std::fflush(stderr);
    }
    return false;
}
'''
def patch(source:str)->tuple[str,int]:
    if (source.count(ARM)!=1 or source.count(RESET)!=1 or
        source.count('V410_NAND_GUEST_RUN_EXIT calls=')!=1 or
        source.count('V405_NAND_SECOND_HALF tail_calls=')!=1 or
        'v411_note_host_stop' in source):
        raise ValueError('geometry')
    sites=0
    def replace(m:re.Match[str])->str:
        nonlocal sites
        if m.group('assignment') is None:
            return m.group(0)
        sites+=1
        # This only labels a lexically adjacent throw, not an executed one.
        throws=int(re.match(r'\s*;\s*throw\s+ExceptionStop\s*\{\s*\}',source[m.end():]) is not None)
        return m.group('assignment')+f'::v411_note_host_stop({sites}u,{throws}u)'
    out=TOKENS.sub(replace,source)
    if not 1<=sites<=9999:
        raise ValueError('sites')
    out=out.replace(ARM,ARM+'\n      ::v411_stop_armed=true;',1)
    out=out.replace(RESET,RESET+'\n  ::v411_stop_armed=false;',1)
    if out.count('::v411_note_host_stop(')!=sites or out.count('::v411_stop_armed=true;')!=1:
        raise ValueError('route')
    return HEADER+out,sites

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prior_harness',type=Path)
    p.add_argument('next_harness',type=Path)
    a=p.parse_args()
    try:
        out,sites=patch(a.prior_harness.read_text(encoding='utf-8'))
        with a.next_harness.open('x',encoding='utf-8') as f:f.write(out)
    except (OSError,ValueError):
        print('V411_HOST_STOP_ROUTE installed=0',file=sys.stderr)
        return 1
    print(f'V411_HOST_STOP_ROUTE installed=1 sites={sites} original_guards=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
