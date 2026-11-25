#!/usr/bin/env python3
"""Strict ordered audit of original restore and epilogue, stopping before BLR."""
import argparse,re
from pathlib import Path
import audit_v870_handler_suffix as old
START=b'V919_RESTORE_START after=6 next=12 kind=1 original_call=1'
ENTRY=b'V919_RESTORE_ENTRY original_target=1'
RETURN=b'V919_RESTORE_RETURN original_return=1 visits=16 gprs=15 follow_held=1'
END=b'V919_HANDLER_EPILOGUE original_restore_return=1 gprs=15 abi=1 blr_boundary=1 handler_return=0 boot_verified=0'
MARKERS=[START,ENTRY,RETURN,END]
def inspect(raw,rc):
    if len(raw)>old.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines()
    hits=[i for i,l in enumerate(rows) if re.fullmatch(old.STOP,l)]
    ok=False
    if rc==0 and len(hits)==1:
        i=hits[0];m=re.fullmatch(old.STOP,rows[i])
        prefix=rows[:i+1];tail=[l for l in rows[i+1:] if l.startswith(old.TAGS+(b'V919_',))]
        _,valid,_=old.inspect(b'\n'.join(prefix),0)
        ok=(valid and m.groups()[:3]==(b'6',b'12',b'1') and old.STATUS in prefix and old.STORE in prefix
            and any(re.fullmatch(old.INDEX,l) for l in prefix)
            and not any(l.startswith(b'V919_') for l in prefix) and tail==MARKERS)
    return f'V919_HANDLER_CENSUS rc={rc} verified={int(ok)} restore_return={int(ok)} gprs={15 if ok else 0} blr_boundary={int(ok)} handler_return=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V919_HANDLER_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in MARKERS or l in (old.STATUS,old.STORE) or any(re.fullmatch(p,l) for p in (old.INDEX,old.JOIN,old.STOP,old.BAD)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
