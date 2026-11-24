#!/usr/bin/env python3
"""Install an opt-in transactional Wii DOL loader in a disposable pinned checkout."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

PINNED_BLOB='67a2b4e5a1d69497f1cf1650dff76f1edd66d949'
FILE=Path('nWiiRuntime/src/core/loader.cpp')
DEST=Path('nWiiRuntime/include/undercover/wii_dol_loader_v431.h')
HEADER='#include "loader/loader.h"'
INCLUDE=HEADER+'\n#include "undercover/wii_dol_loader_v431.h"'
START='bool Executable::load_dol(const std::string& path) {'
NEXT='bool Executable::load_rel('
NEW=START+'''
    std::ifstream file(path, std::ios::binary);
    return file.is_open() && undercover::wii::load_strict_dol(file,entry_point,sections);
}

'''

def blob(source:str)->str:
    data=source.encode('utf-8');return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()

def rewrite(source:str,expected:str=PINNED_BLOB)->str:
    if source.count(INCLUDE)==1 and source.count(NEW)==1:
        if source.count(START)!=1 or source.count(NEXT)!=1:raise ValueError('ambiguous patched loader')
        return source
    if 'undercover::wii::load_strict_dol' in source or INCLUDE in source or blob(source)!=expected:raise ValueError('unknown loader revision')
    if any(source.count(x)!=1 for x in (HEADER,START,NEXT)):raise ValueError('loader geometry')
    start,end=source.index(START),source.index(NEXT)
    if start>=end or not source[start:end].endswith('}\n\n'):raise ValueError('loader extent')
    out=source[:start]+NEW+source[end:]
    return out.replace(HEADER,INCLUDE,1)

def apply(root:Path,expected:str=PINNED_BLOB)->bool:
    src=root/FILE;dest=root/DEST;host=Path(__file__).with_name(DEST.name)
    if src.is_symlink() or dest.is_symlink() or dest.parent.is_symlink():raise ValueError('symlink')
    original=src.read_text(encoding='utf-8');out=rewrite(original,expected)
    header=host.read_text(encoding='utf-8')
    if out==original:
        if not dest.is_file() or dest.read_text(encoding='utf-8')!=header:raise ValueError('inconsistent installation')
        return False
    if dest.exists():raise ValueError('destination exists')
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(header,encoding='utf-8');src.write_text(out,encoding='utf-8');return True

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    try:changed=apply(a.root)
    except (OSError,ValueError,UnicodeError):
        print('V431_DOL_LOADER installed=0');return 1
    print(f'V431_DOL_LOADER installed=1 changed={int(changed)} transactional=1');return 0
if __name__=='__main__':raise SystemExit(main())
