#!/usr/bin/env python3
"""Privacy-safe V407 original Wii 96-call abort provenance categories.

Read only private scratch logs and the original-free host harness.
Reuse V307's known PUBLIC assertion matching, but never output assertion
messages, private original guest code, native registers or original paths.
A signal classification does not establish a new guest-call milestone.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
from analyze_v307_helper_abort import inspect as classify_public_abort

SUMMARY=re.compile(
    r'^V307_ABORT_PROVENANCE rc=([0-9]{1,3}) '
    r'kind=(zero|nonzero|timeout|signal|launch) '
    r'size_band=([0-3]) callback=([01]) child=([01]) early=([01]) '
    r'public_id=([0-9]{4}) known=([01]) '
    r'exception=(runtime|logic|range|alloc|unclassified)$')
ALLOWED=('v404','v405')

def inspect(path:Path,harness:Path,rc:int,candidate:str)->str:
    if candidate not in ALLOWED:
        raise ValueError('invalid_candidate')
    if rc<0 or rc>255:
        raise ValueError('invalid_status')
    public_source=harness.read_text(encoding='utf-8',errors='replace')
    summary,_=classify_public_abort(path,public_source,rc)
    m=SUMMARY.fullmatch(summary)
    if not m or int(m.group(1))!=rc:
        raise ValueError('invalid_public_abort_summary')
    _,kind,band,callback,_child,_early,ident,known,exception=m.groups()
    if (int(known)!=int(int(ident)>0)):
        raise ValueError('invalid_public_provenance')
    return (
        f'V407_NATIVE_ABORT_CLASS candidate={candidate} rc={rc} '
        f'kind={kind} size_band={band} known_public={known} '
        f'exception={exception} callback={callback} '
        f'boot_verified=0'
    )
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_native_log',type=Path)
    p.add_argument('private_original_free_host_harness',type=Path)
    p.add_argument('native_exit_code',type=int)
    p.add_argument('candidate',choices=ALLOWED)
    a=p.parse_args()
    try:
        print(inspect(a.private_native_log,
                      a.private_original_free_host_harness,
                      a.native_exit_code,a.candidate))
    except (OSError,ValueError):
        print('V407_NATIVE_ABORT_AUDIT inspected=0',file=sys.stderr)
        return 1
    print('V407_NATIVE_ABORT_AUDIT inspected=1')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
