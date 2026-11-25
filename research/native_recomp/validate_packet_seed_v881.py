#!/usr/bin/env python3
"""Validate private runtime-discovered fixture address geometry without printing it."""
import argparse
from pathlib import Path

def validate(rows):
    if len(rows)!=8 or rows[:4]!=rows[4:]:raise ValueError('repeat')
    stride=rows[1]-rows[0]
    if stride<4 or stride>128 or stride%4 or rows[:4]!=[rows[0]+i*stride for i in range(4)]:raise ValueError('stride')
    if not all(a%4==0 and a!=0x80619a60 and (0x80619a60<=a<=0x8061aa5c or 0x8070d000<=a<=0x8070e8fc) for a in rows):raise ValueError('region')
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
    try:
        rows=[]
        for i in range(8):
            f=a.directory/f'{i}.txt'
            if f.is_symlink() or not f.is_file() or f.stat().st_size>64:raise ValueError('file')
            rows.append(int(f.read_text().strip()))
        validate(rows)
    except (ValueError,OSError,UnicodeError):print('V881_PACKET_SEED verified=0');return 1
    print('V881_PACKET_SEED verified=1 channels=4 repeated=1 stride=1 private=1');return 0
if __name__=='__main__':raise SystemExit(main())
