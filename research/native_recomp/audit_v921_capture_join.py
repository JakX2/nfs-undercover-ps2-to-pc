#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v920_handler_return as old
import audit_v751_cold_capture as capture
RETURN=b'V921_SAVED_CONTEXT_RETURN original_snapshot=1 saved_gprs=32 special=6 same_cpu=1 unchanged=1 rfi_return=0 boot_verified=0'
def inspect(raw,rc):
    if len(raw)>capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();entry=[i for i,l in enumerate(rows) if l==capture.RESULT];returned=[i for i,l in enumerate(rows) if l==old.RETURN]
    ok=False
    if rc==0 and len(entry)==len(returned)==1 and entry[0]<returned[0]:
        i,j=entry[0],returned[0]
        _,cap=capture.inspect(b'\n'.join(rows[:i+1]),0)
        _,ret=old.inspect(b'\n'.join(rows[:j+1]),0)
        tags=old.old.old.TAGS+(b'V919_',b'V920_',b'V921_',capture.PREFIX)
        tail=[l for l in rows[j+1:] if l.startswith(tags)]
        ok=cap and ret and tail==[RETURN] and not any(l.startswith(capture.PREFIX) for l in rows[i+1:]) and not any(l.startswith(b'V921_') for l in rows[:j+1])
    return f'V921_CONTEXT_CENSUS rc={rc} verified={int(ok)} original_snapshot={int(ok)} handler_return={int(ok)} saved_gprs={32 if ok else 0} special={6 if ok else 0} rfi_return=0 boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V921_CONTEXT_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (*capture.CAPTURE,*old.old.MARKERS,old.POLL,old.RETURN,RETURN,old.old.old.STATUS,old.old.old.STORE) or any(re.fullmatch(p,l) for p in (old.old.old.INDEX,old.old.old.JOIN,old.old.old.STOP,old.old.old.BAD)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
