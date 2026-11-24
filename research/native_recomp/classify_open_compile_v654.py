#!/usr/bin/env python3
"""Classify isolated fixture compiler failures without disclosing generated code."""
import argparse
from pathlib import Path
def classify(raw):
    if len(raw)>16*1024*1024:return 'oversize'
    s=raw.decode('utf-8','replace')
    if 'redefinition of' in s and 'OpenCacheRangeTrace' in s:return 'cache_header_duplicate'
    if 'undefined reference' in s:return 'link'
    if 'No such file or directory' in s:return 'missing_include'
    if 'was not declared in this scope' in s:return 'missing_symbol'
    if 'has no member named' in s:return 'missing_member'
    if 'error:' in s:return 'compile_other'
    return 'unknown'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);a=p.parse_args()
    try:
        kind='oversize' if a.log.stat().st_size>16*1024*1024 else classify(a.log.read_bytes())
    except OSError:kind='unknown'
    print('V654_OPEN_COMPILE_DIAG kind='+kind)
