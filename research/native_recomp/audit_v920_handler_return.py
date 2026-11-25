#!/usr/bin/env python3
"""Require real original handler BLR, return poll and original dispatcher resume."""
import argparse
from pathlib import Path
import audit_v919_handler_epilogue as old
POLL=b'V920_HANDLER_POLL original_blr=1 same_tick=1'
RETURN=b'V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>old.old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l==old.END]
    ok=False
    if rc==0 and len(hits)==1:
        i=hits[0];prefix=rows[:i+1]
        _,valid=old.inspect(b'\n'.join(prefix),0)
        tags=old.old.TAGS+(b'V919_',b'V920_')
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        ok=valid and not any(l.startswith(b'V920_') for l in prefix) and tail==[POLL,RETURN]
    return f'V920_HANDLER_CENSUS rc={rc} verified={int(ok)} handler_return={int(ok)} dispatcher_resume={int(ok)} abi={int(ok)} rfi_return=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V920_HANDLER_AUDIT inspected=0');return 1
    # Reuse the allowlisted V919 parser on the preceding stage.
    import re
    for l in raw.splitlines():
        if l in (*old.MARKERS,POLL,RETURN,old.old.STATUS,old.old.STORE) or any(re.fullmatch(p,l) for p in (old.old.INDEX,old.old.JOIN,old.old.STOP,old.old.BAD)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
