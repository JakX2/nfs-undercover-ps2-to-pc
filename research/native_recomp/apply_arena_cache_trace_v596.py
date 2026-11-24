#!/usr/bin/env python3
"""Opt-in constant-space arena observation on actual native cache methods."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_dcbz_v67 import NEW_INCLUDE,NEW_CTX
FILE=Path('nWiiRuntime/include/runtime/cpu_context.h')
HEADER='undercover/arena_cache_range_trace_v596.h'
INCLUDE='#include "flat_cacheline_zero_v67.h"'
ZERO='  void guest_dcbz(uint32_t ea) { guest_dcbz_trace.zero(mmu,ea); }'
FLUSH='  void guest_dcbf(uint32_t effective_address) {\n    const uint32_t line = effective_address & ~31u;'
PAIRS=((INCLUDE,INCLUDE+'\n#include "'+HEADER+'"'),
       (ZERO,'  undercover::wii::ArenaCacheRangeTrace arena_cache_range;\n  void guest_dcbz(uint32_t ea) { arena_cache_range.on_zero(ea); guest_dcbz_trace.zero(mmu,ea); }'),
       (FLUSH,FLUSH+'\n    arena_cache_range.on_flush(effective_address);'))
def apply(root,host):
    p=root/FILE;dest=p.parent.parent/HEADER
    if p.is_symlink() or dest.is_symlink() or dest.parent.is_symlink():raise ValueError('symlink')
    old=p.read_text(encoding='utf-8');new=rewrite(old,PAIRS)
    data=(host/Path(HEADER).name).read_text(encoding='utf-8')
    if dest.exists() and dest.read_text(encoding='utf-8')!=data:raise ValueError('header identity')
    if new==old and not dest.is_file():raise ValueError('partial installation')
    if new!=old:
        dest.parent.mkdir(exist_ok=True);dest.write_text(data,encoding='utf-8');p.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    try:apply(a.root,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError):print('V596_ARENA_CACHE_ROUTE installed=0');return 1
    print('V596_ARENA_CACHE_ROUTE installed=1 default_inactive=1 constant_space=1');return 0
if __name__=='__main__':raise SystemExit(main())
