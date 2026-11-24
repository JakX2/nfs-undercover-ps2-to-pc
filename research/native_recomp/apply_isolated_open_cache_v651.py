#!/usr/bin/env python3
"""Isolated cache event hook; no prior arena lane in this fixture."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
INC='#include "runtime/guest_memory.h"'
FLUSH='  void guest_dcbf(uint32_t effective_address) {\n    const uint32_t line = effective_address & ~31u;'
def apply(root,host):
    p=root/'nWiiRuntime/include/runtime/cpu_context.h';s=p.read_text()
    # Include before the CPU namespace rather than assuming an unrelated
    # upstream include. The V561 cache patch establishes this exact seam.
    anchor='#pragma once'
    pairs=((anchor,anchor+'\n#include "undercover/open_cache_range_trace_v649.h"'),
           (FLUSH,'  undercover::wii::OpenCacheRangeTrace open_cache_range;\n'+FLUSH+'\n    open_cache_range.on_flush(effective_address);'))
    out=rewrite(s,pairs)
    dest=root/'nWiiRuntime/include/undercover';dest.mkdir(exist_ok=True)
    (dest/'open_cache_range_trace_v649.h').write_text((host/'open_cache_range_trace_v649.h').read_text())
    p.write_text(out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();apply(a.root,Path(__file__).parent)
