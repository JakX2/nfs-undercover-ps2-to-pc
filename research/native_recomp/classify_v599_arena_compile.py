#!/usr/bin/env python3
"""Emit only allowlisted public source basenames, line numbers and error categories."""
import re,sys
from pathlib import Path
PUBLIC={'test_native_arena_sc_v598.cpp','wii_arena_sc_pair_v598.h','arena_cache_range_trace_v596.h',
        'cpu_context.h','flat_cacheline_zero_v67.h','wii_boot_sc_route_v570.h'}
def classify(raw):
    rows=set()
    for line in raw.splitlines():
        m=re.match(r'^.*[/\\]([A-Za-z0-9_]+\.(?:h|cpp)):(\d+):\d+: (?:fatal )?error: (.*)$',line)
        if not m:continue
        file,n,msg=m.groups()
        if file not in PUBLIC:continue
        kind=next((k for k,v in [('redefinition','redefinition'),('missing_member','has no member'),('type','cannot convert'),('declaration','not declared'),('include','No such file'),('overload','no matching function'),('template','template')] if v in msg),'other')
        rows.add((file,int(n),kind))
    return sorted(rows)[:16]
if __name__=='__main__':
    p=Path(sys.argv[1])
    if p.stat().st_size>8*1024*1024:print('V599_ARENA_COMPILE bounded=0');sys.exit(0)
    rows=classify(p.read_text(errors='replace'))
    for file,n,kind in rows:print(f'V599_ARENA_COMPILE file={file} line={n} kind={kind}')
    print(f'V599_ARENA_COMPILE diagnostics={len(rows)} bounded=1')
