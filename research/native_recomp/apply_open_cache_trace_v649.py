#!/usr/bin/env python3
"""Attach a separate read-only open cache trace to already instrumented RAM."""
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
FILE=Path('nWiiRuntime/include/runtime/cpu_context.h')
HEADER='undercover/open_cache_range_trace_v649.h'
INC='#include "undercover/arena_cache_range_trace_v596.h"'
ZERO='  void guest_dcbz(uint32_t ea) { arena_cache_range.on_zero(ea); guest_dcbz_trace.zero(mmu,ea); }'
FLUSH='    arena_cache_range.on_flush(effective_address);'
PAIRS=((INC,INC+'\n#include "'+HEADER+'"'),
       (ZERO,'  undercover::wii::OpenCacheRangeTrace open_cache_range;\n  void guest_dcbz(uint32_t ea) { open_cache_range.on_zero(ea); arena_cache_range.on_zero(ea); guest_dcbz_trace.zero(mmu,ea); }'),
       (FLUSH,FLUSH+'\n    open_cache_range.on_flush(effective_address);'))
def apply(root,host):
    p=root/FILE;dest=p.parent.parent/HEADER
    if p.is_symlink() or dest.is_symlink() or dest.parent.is_symlink():raise ValueError('open cache symlink')
    s=p.read_text(encoding='utf-8');out=rewrite(s,PAIRS)
    h=(host/Path(HEADER).name).read_text(encoding='utf-8')
    if dest.exists() and dest.read_text(encoding='utf-8')!=h:raise ValueError('open cache header identity')
    if out==s and not dest.is_file():raise ValueError('open cache partial install')
    if out!=s:dest.write_text(h,encoding='utf-8');p.write_text(out,encoding='utf-8')
