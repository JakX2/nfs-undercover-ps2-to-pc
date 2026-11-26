#!/usr/bin/env python3
"""Distinct terminal gates for successful and no-response helper returns."""
import argparse,re,tempfile,sys
from pathlib import Path
import audit_v989_shared_time as shared
RESULT=b'V1015_ERROR_HELPER_RETURN original_helper_return=1 no_response=1 shared_time=0 entries=6 returns=6 msr=2 visits=130 token_preserved=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>shared.old.old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l.startswith(b'V1015_')]
    if not hits:
        _,ok=shared.inspect(raw,rc)
        return f'V1015_COMPLETION_CENSUS verified={int(ok)} no_response=0 shared_time={int(ok)} boot_verified=0',ok,raw
    i=hits[0];prior=b'\n'.join(rows[:i])
    tags=shared.old.old.old.handler.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V932_',b'V939_',b'V951_',b'V958_',b'V967_',b'V975_',b'V981_',b'V989_',b'V995_',b'V1009_',b'V1014_',b'V1015_',shared.old.old.old.capture.PREFIX)
    _,base=shared.old.inspect(prior,rc)
    post=[l for l in rows[:i] if re.fullmatch(shared.old.RESULT,l)]
    ok=bool(rc==0 and len(hits)==1 and rows[i]==RESULT and base and
        len(post)==1 and re.fullmatch(shared.old.RESULT,post[0])[1]==b'130' and
        not any(l.startswith((b'V975_',b'V981_',b'V989_',b'V995_',b'V1009_',b'V1014_')) for l in rows[:i]) and
        not any(l.startswith(tags) for l in rows[i+1:]))
    return f'V1015_COMPLETION_CENSUS verified={int(ok)} no_response={int(ok)} shared_time=0 boot_verified=0',ok,prior
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>shared.old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok,prior=inspect(raw,a.rc)
    except (OSError,ValueError):print('V1015_COMPLETION_AUDIT inspected=0');return 1
    with tempfile.TemporaryDirectory() as td:
        log=Path(td)/'prior';log.write_bytes(prior)
        previous=sys.argv;sys.argv=[previous[0],str(log),str(a.rc)]
        try:
            if any(l.startswith(b'V1015_') for l in raw.splitlines()):shared.old.main()
            else:shared.main()
        finally:sys.argv=previous
    for l in raw.splitlines():
        if l==RESULT or re.fullmatch(shared.DETAIL,l):print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
