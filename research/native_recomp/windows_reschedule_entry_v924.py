#!/usr/bin/env python3
"""Strict complete-image reschedule-entry evidence after real scheduler return."""
from __future__ import annotations
from windows_scheduler_return_v923 import inspect as earlier,RESULT as PREDECESSOR,diagnostic as diag
from windows_startup_scope_v434 import MAX_LOG

RESULT=(b'V924_WINDOWS_RESCHEDULE_ENTRY original_handler_return=1 scheduler_return=1 '
        b'original_reschedule_branch=1 native_entry_tick=1 reschedule_return=0 rfi=0 boot_verified=0')

def inspect(raw:bytes,rc:int,timed_out:bool=False)->tuple[str,bool]:
    if type(raw) is not bytes or len(raw)>MAX_LOG or type(rc) is not int or type(timed_out) is not bool:
        raise ValueError('reschedule entry contract')
    rows=raw.splitlines();matches=[i for i,line in enumerate(rows) if line==PREDECESSOR]
    returned=False
    if len(matches)==1 and not timed_out:
        prefix=b'\n'.join(rows[:matches[0]+1])+b'\n'
        _,returned=earlier(prefix,0)
    ok=bool(returned and rc==0 and not timed_out and rows[matches[0]+1:]==[RESULT])
    kind='timeout' if timed_out else 'zero' if rc==0 else 'exception' if rc<0 or rc>=0xC0000000 else 'other'
    return (f'V924_WINDOWS_RESCHEDULE exit={kind} scheduler_return={int(returned)} '
            f'reschedule_entry={int(ok)} native_tick={int(ok)} rfi=0 boot_verified=0',ok)

def diagnostic(line:bytes)->bool:
    return type(line) is bytes and diag(line)
