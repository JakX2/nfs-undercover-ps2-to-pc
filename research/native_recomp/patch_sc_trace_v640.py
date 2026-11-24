#!/usr/bin/env python3
"""Make the precise pre-SC trace report the actual guest instruction PC.

The V26 emitter already assigns the same PC immediately after the trace.
No guest instruction is replaced, and no execution state is changed on
any other label. Opt-in only for the first IOS_Open continuation.
"""
import argparse
from pathlib import Path
from patch_sc_trace_v570 import TRACE,PAT
NEW='    if (nwii::runtime::g_trace_calls) { ctx.pc = 0x805222E8; nwii::runtime::trace_call(0x805222E8, ctx); } // V640 exact pre-SC PC\n'
def rewrite(source):
    if source.count(NEW)==1 and TRACE not in source:return source
    # Require the exact authenticated label, prior trace and native tick.
    anchor='loc_805222E8: ;\n    // 0x805222E8: 44000002\n'+TRACE+'    ++ctx.inst_count;\n'
    if source.count(anchor)!=1 or source.count(TRACE)!=1 or NEW in source:raise ValueError('SC trace identity')
    return source.replace(TRACE,NEW,1)
def install(root):
    rows=[]
    for p in root.glob('output_*.cpp'):
        if p.is_symlink():raise ValueError('symlink')
        s=p.read_text(encoding='utf-8')
        if TRACE in s or NEW in s:rows.append((p,rewrite(s)))
    if len(rows)!=1:raise ValueError('unique pre-SC trace')
    p,s=rows[0];p.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('generated',type=Path);a=p.parse_args()
    try:install(a.generated)
    except (OSError,ValueError,UnicodeError):print('V640_SC_TRACE installed=0');return 1
    print('V640_SC_TRACE installed=1 exact_pc=1');return 0
if __name__=='__main__':raise SystemExit(main())
