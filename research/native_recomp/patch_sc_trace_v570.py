#!/usr/bin/env python3
"""Inject a trace immediately before the exact emitted cache-flush SC label."""
import argparse,re
from pathlib import Path
PAT=re.compile(r'(?m)^loc_805222E8: ;\n    // 0x805222E8: 44000002\n(?=    \+\+ctx\.inst_count;)')
TRACE='    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x805222E8, ctx); // V570 pre-SC trace\n'
def patch(source):
    if len(PAT.findall(source))!=1 or TRACE in source:raise ValueError('SC trace geometry')
    return PAT.sub(lambda m:m[0]+TRACE,source,count=1)
def install(root):
    paths=[]
    for p in root.glob('output_*.cpp'):
        if p.is_symlink():raise ValueError('symlink')
        s=p.read_text(encoding='utf-8')
        if PAT.search(s):paths.append((p,patch(s)))
    if len(paths)!=1:raise ValueError('unique SC trace')
    p,s=paths[0];p.write_text(s,encoding='utf-8')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    try:install(a.root)
    except (OSError,ValueError,UnicodeError):print('V570_TRACE installed=0');raise SystemExit(1)
    print('V570_TRACE installed=1')
