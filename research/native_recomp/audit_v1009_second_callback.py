#!/usr/bin/env python3
"""Require the V995 known target and one subsequent verified prefix."""
import argparse,re,tempfile,sys
from pathlib import Path
import audit_v995_success_frontier as old
RESULT=rb'V1009_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes=8 visits=13 token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0'
FAULT=rb'V958_ACK_INVALID kind=14 stage=[0-4] reason=[0-5] call_reason=[0-5] visits=[0-9]{1,4}'
def inspect(raw,rc):
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l.startswith(b'V1009_')]
    prior=raw;prefix=0
    if hits:
        if len(hits)!=1 or not re.fullmatch(RESULT,rows[hits[0]]):return 'V1009_CALLBACK_CENSUS verified=0 prefix=0 boot_verified=0',False,raw
        i=hits[0]
        if any(l.startswith(old.TAGS+(b'V1009_',)) for l in rows[i+1:]):return 'V1009_CALLBACK_CENSUS verified=0 prefix=0 boot_verified=0',False,raw
        prior=b'\n'.join(rows[:i])
        selected=[re.fullmatch(old.RESULT,l) for l in rows[:i] if l.startswith(b'V995_')]
        if len(selected)!=1 or not selected[0] or selected[0].groups()[:2]!=(b'2',b'1'):return 'V1009_CALLBACK_CENSUS verified=0 prefix=0 boot_verified=0',False,raw
        prefix=1
    line,ok=old.inspect(prior,rc)
    # In this mode a known aligned target must actually execute the prefix.
    if 'branch=6 admitted=1' in line and not prefix:ok=False
    return f'V1009_CALLBACK_CENSUS verified={int(ok)} prefix={prefix if ok else 0} boot_verified=0',ok,prior
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.shared.old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok,prior=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1009_CALLBACK_AUDIT inspected=0');return 1
    # Existing audit only emits allowlisted sanitized lines.
    with tempfile.TemporaryDirectory() as td:
        log=Path(td)/'prior';log.write_bytes(prior)
        previous=sys.argv;sys.argv=[previous[0],str(log),str(a.rc)]
        try:old.main()
        finally:sys.argv=previous
    for line in raw.splitlines():
        if re.fullmatch(RESULT,line) or re.fullmatch(FAULT,line):print(line.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
