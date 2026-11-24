#!/usr/bin/env python3
"""Match PowerPC LR/CTR target alignment in the pinned native emitter.

Preserve BO, BI, CTR and LR ordering, and the existing exact-zero linked
CTR compatibility guard. Nonzero valid targets discard low two bits.
"""
import argparse
from pathlib import Path
FILE=Path('nWiiRecomp/src/recompiler.cpp')
TARGET='      std::string target_reg = (xo == 16) ? "ctx.lr" : "ctx.ctr";'
TARGET_NEW=TARGET+'\n      const std::string target_addr = "(" + target_reg + " & ~3u)";'
TEMP='out << "        uint32_t temp_lr = ctx.lr;\\n";'
TEMP_NEW=TEMP.replace('ctx.lr;','ctx.lr & ~3u;')
PC='ctx.pc = " << target_reg'
PC_NEW='ctx.pc = " << target_addr'
PAIRS=((TARGET,TARGET_NEW,1),(TEMP,TEMP_NEW,1),(PC,PC_NEW,4))
def rewrite(s):
    if all(s.count(b)==n for a,b,n in PAIRS):
        back=s
        for a,b,n in reversed(PAIRS):back=back.replace(b,a)
        if all(back.count(a)==n and b not in back for a,b,n in PAIRS):return s
        raise ValueError('mixed alignment')
    if not all(s.count(a)==n and b not in s for a,b,n in PAIRS):raise ValueError('unknown or mixed alignment source')
    out=s
    for a,b,n in PAIRS:out=out.replace(a,b)
    back=out
    for a,b,n in reversed(PAIRS):back=back.replace(b,a)
    if back!=s:raise ValueError('roundtrip')
    return out
def apply(root):
    p=root/FILE
    if p.is_symlink():raise ValueError('symlink')
    old=p.read_text(encoding='utf-8');new=rewrite(old)
    if old==new:return False
    p.write_text(new,encoding='utf-8');return True
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    print(f'V467_BRANCH_ALIGNMENT installed=1 changed={int(apply(a.root))}')
