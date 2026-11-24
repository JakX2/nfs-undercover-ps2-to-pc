#!/usr/bin/env python3
"""Propagate a stopped guest CPU through native callers and dispatch.

Use after V461 (or an equivalent syscall transfer patch). Never alter
guest PC, LR or register state. Preserve ordinary return-PC checks.
"""
import argparse
from pathlib import Path
FILE=Path('nWiiRecomp/src/recompiler.cpp')
DIRECT='''          out << "    if (ctx.pc != 0x" << std::hex << std::uppercase
              << (inst.address + 4) << std::dec << ") return;\\n";'''
MICRO='''    out << "    if (ctx.pc != 0x" << std::hex << (inst.address + 4) << std::dec
        << ") return;\\n";'''
DISPATCH='''    out << "        process_pending_callbacks(ctx);\\n";'''
PAIRS=((DIRECT,DIRECT.replace('if (ctx.pc','if (!ctx.is_running || ctx.pc'),1),
       (MICRO,MICRO.replace('if (ctx.pc','if (!ctx.is_running || ctx.pc'),1),
       (DISPATCH,DISPATCH+'\n    out << "        if (!ctx.is_running) break;\\n";',2))
# The dispatcher anchor is a substring of its replacement; use a
# reverse roundtrip to identify a wholly installed version.
def rewrite(source):
    if all(source.count(b)==n for a,b,n in PAIRS):
        back=source
        for a,b,n in reversed(PAIRS):back=back.replace(b,a)
        if all(back.count(a)==n and b not in back for a,b,n in PAIRS):return source
        raise ValueError('mixed stop guard')
    if not all(source.count(a)==n and b not in source for a,b,n in PAIRS):raise ValueError('unknown or mixed stop guard')
    out=source
    for a,b,n in PAIRS:out=out.replace(a,b)
    back=out
    for a,b,n in reversed(PAIRS):back=back.replace(b,a)
    if back!=source:raise ValueError('roundtrip')
    return out
def apply(root):
    path=root/FILE
    if path.is_symlink():raise ValueError('symlink')
    old=path.read_text(encoding='utf-8');new=rewrite(old)
    if old==new:return False
    path.write_text(new,encoding='utf-8');return True
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    print(f'V463_NATIVE_STOP installed=1 changed={int(apply(a.root))}')
