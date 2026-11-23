#!/usr/bin/env python3
"""Strict V405 16x48 successor-region census, independent native owner run."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from analyze_v405_nand_second_half import inspect as census
from audit_v404_nand_extended import verify as original_96

NUMBER=r'([0-9]{1,3})'
RESULT=re.compile(
    r'^V405_NAND_SECOND_CENSUS rc=0 kind=zero size_band=[0-3] '
    r'sample_complete=[01] entries=16 trials=16 max_tail=48 '
    r'full48_trials=16 '
    + ' '.join(f'{label}_total={NUMBER}' for label in
               ('selected','isfs','parent','other','nand','cache'))
    +r' lineage_verified=1 boot_verified=0$'
)
def verify(path:Path,rc:int)->tuple[bool,int,int,int,int]:
    if rc!=0 or not original_96(path,rc):
        return False,0,0,0,0
    m=RESULT.fullmatch(census(path,rc))
    if not m:
        return False,0,0,0,0
    selected,isfs,parent,other,nand,cache=map(int,m.groups())
    valid=(selected+isfs+parent+other==768 and
           nand<=768 and cache<=768)
    return bool(valid),int(valid and isfs>0),int(valid and parent>0),int(valid and nand>0),int(valid and cache>0)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_original_log',type=Path)
    p.add_argument('native_exit_code',type=int)
    a=p.parse_args()
    try:valid,isfs,parent,nand,cache=verify(a.private_original_log,a.native_exit_code)
    except (ValueError,OSError):valid,isfs,parent,nand,cache=False,0,0,0,0
    print(f'V405_OWNER_RESULT_GATE verified={int(valid)} '
          f'isfs_any={isfs} parent_any={parent} '
          f'nand_any={nand} cache_any={cache} boot_verified=0')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
