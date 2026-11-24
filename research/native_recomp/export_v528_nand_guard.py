#!/usr/bin/env python3
"""Publish only the bounded V517 guard census, never owner log strings."""
import argparse
from pathlib import Path
import re
from derive_v478_nand_post_return import GUARD_CLASSES
CLASSES=set(GUARD_CLASSES.values())|{'other','unknown'}
HEAD=re.compile(rb'V517_NAND_NEXT_GUARD aborted=1 id=([0-9]{4}) class=([a-z_]{1,32}) matches=([0-9]{1,4}) boot_verified=0')
SOURCE=re.compile(rb'V517_NAND_GUARD_SOURCE id=([0-9]{4}) n=([1-8]) file=([A-Za-z0-9_]{1,100}\.(?:py|cpp|h)) line=([1-9][0-9]{0,6}) boot_verified=0')
ABORT=re.compile(rb'V508_ABORT_CENSUS rc=134 public_id=([0-9]{4}) known=[01] category=[a-z_]{1,32} exception=[a-z_]{1,32} boot_verified=0')
def select(raw,host):
    if len(raw)>64*1024*1024:raise ValueError('size')
    lines=raw.splitlines()
    heads=[l for l in lines if l.startswith(b'V517_NAND_NEXT_GUARD ')]
    rows=[l for l in lines if l.startswith(b'V517_NAND_GUARD_SOURCE ')]
    aborts={m[1] for l in lines if (m:=ABORT.fullmatch(l))}
    if len(heads)!=1:raise ValueError('head count')
    if heads[0]==b'V517_NAND_NEXT_GUARD aborted=0 boot_verified=0':
        if rows or aborts:raise ValueError('unexpected abort')
        return tuple(heads)
    m=HEAD.fullmatch(heads[0])
    if not m or m[2].decode() not in CLASSES or aborts!={m[1]}:raise ValueError('head')
    count=int(m[3])
    if len(rows)!=(count if 1<=count<=8 else 0):raise ValueError('source count')
    seen=set()
    for i,l in enumerate(rows,1):
        s=SOURCE.fullmatch(l)
        if not s or s[1]!=m[1] or int(s[2])!=i:raise ValueError('source geometry')
        name=s[3].decode();line=int(s[4]);p=host/name
        if name.startswith('test_') or p.is_symlink() or not p.is_file() or p.stat().st_size>2_000_000:raise ValueError('source path')
        if line>len(p.read_bytes().splitlines()) or (name,line) in seen:raise ValueError('source line')
        seen.add((name,line))
    return tuple(heads+rows)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);a=p.parse_args()
    try:
        if a.log.stat().st_size>64*1024*1024:raise ValueError('size')
        for row in select(a.log.read_bytes(),Path(__file__).resolve().parent):print(row.decode('ascii'))
    except (OSError,ValueError,UnicodeError):
        print('V528_NAND_EXPORT verified=0');return 1
    print('V528_NAND_EXPORT verified=1');return 0
if __name__=='__main__':raise SystemExit(main())
