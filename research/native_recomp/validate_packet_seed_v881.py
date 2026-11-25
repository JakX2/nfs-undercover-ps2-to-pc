#!/usr/bin/env python3
"""Validate private runtime-discovered fixture address geometry without printing it."""
import argparse
from pathlib import Path

def validate(rows):
    if len(rows)!=8 or rows[:4]!=rows[4:]:raise ValueError('repeat')
    addresses=[a for a,_ in rows]
    sections={s for _,s in rows}
    stride=addresses[1]-addresses[0]
    if stride<4 or stride>128 or stride%4 or addresses[:4]!=[addresses[0]+i*stride for i in range(4)]:raise ValueError('stride')
    if len(sections)!=1 or not 1<=next(iter(sections))<=64 or not all(a%4==0 and a!=0x80619a60 and 0x80000000<=a<=0x817ffffc for a in addresses):raise ValueError('region')
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
    try:
        rows=[]
        for i in range(8):
            f=a.directory/f'{i}.txt'
            if f.is_symlink() or not f.is_file() or f.stat().st_size>64:raise ValueError('file')
            v=f.read_text().split()
            if len(v)!=2:raise ValueError('file')
            rows.append(tuple(map(int,v)))
        validate(rows)
    except (ValueError,OSError,UnicodeError):print('V881_PACKET_SEED verified=0');return 1
    print('V881_PACKET_SEED verified=1 channels=4 repeated=1 stride=1 private=1');return 0
if __name__=='__main__':raise SystemExit(main())
