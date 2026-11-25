#!/usr/bin/env python3
import argparse,re
from pathlib import Path
import audit_v928_leaf_finish as old
BEGIN=b'V930_IPC_BEGIN cold_prerequisites=1 original_call=1'
RETURN=b'V930_IPC_ENTRY original_bl=1 original_target=1 cold_prerequisites=1 same_tick=1 device_held=1 ipc_instruction_executed=0 boot_verified=0'
FAULT=rb'V930_IPC_INVALID kind=[1-3] ipc=[0-7] join=[0-2] stage=[0-2]'
def inspect(raw,rc):
    if len(raw)>old.old.old.capture.MAX_LOG or not 0<=rc<=255:raise ValueError('geometry')
    rows=raw.splitlines();hits=[i for i,l in enumerate(rows) if l==old.RETURN];ok=False
    if rc==0 and len(hits)==1:
        i=hits[0];_,valid=old.inspect(b'\n'.join(rows[:i+1]),0)
        tags=old.old.old.old.old.old.TAGS+(b'V919_',b'V920_',b'V921_',b'V922_',b'V928_',b'V930_',old.old.old.capture.PREFIX)
        tail=[l for l in rows[i+1:] if l.startswith(tags)]
        ok=bool(valid and tail==[BEGIN,RETURN] and not any(l.startswith(b'V930_') for l in rows[:i+1]))
    return f'V930_IPC_CENSUS rc={rc} verified={int(ok)} original_entry={int(ok)} cold_prerequisites={int(ok)} boot_verified=0',ok
def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('rc',type=int);a=p.parse_args()
    try:
        if a.log.stat().st_size>old.old.old.capture.MAX_LOG:raise ValueError('size')
        raw=a.log.read_bytes();row,ok=inspect(raw,a.rc)
    except (OSError,ValueError):print('V930_IPC_AUDIT inspected=0');return 1
    for l in raw.splitlines():
        if l in (old.BEGIN,old.BLR,old.POLL,old.RETURN,BEGIN,RETURN,*old.old.STAGES) or any(re.fullmatch(p,l) for p in (old.old.RESULT,old.old.FAULT,old.FAULT,FAULT)):
            print(l.decode())
    print(row);return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
