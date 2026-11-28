#!/usr/bin/env python3
"""Require real original scheduler-enable return before original reschedule."""
from __future__ import annotations
from windows_scheduler_entry_v922 import inspect as predecessor, RESULT as ENTRY, diagnostic as prior_diag
from windows_startup_scope_v434 import MAX_LOG

RESULT=(b'V923_WINDOWS_SCHEDULER_RETURN original_handler_return=1 original_enable=1 '
        b'disable=1 restore=1 counter=1 abi=1 reschedule_executed=0 rfi=0 boot_verified=0')

def inspect(raw:bytes,rc:int,timed_out:bool=False)->tuple[str,bool]:
    if type(raw) is not bytes or len(raw)>MAX_LOG or type(rc) is not int or type(timed_out) is not bool:
        raise ValueError('scheduler return log contract')
    rows=raw.splitlines();matches=[i for i,row in enumerate(rows) if row==ENTRY]
    before=False
    if len(matches)==1 and rc==0 and not timed_out:
        prefix=b'\n'.join(rows[:matches[0]+1])+b'\n'
        _,before=predecessor(prefix,0)
    ok=bool(before and rows[matches[0]+1:]==[RESULT])
    kind='timeout' if timed_out else 'zero' if rc==0 else 'exception' if rc<0 or rc>=0xC0000000 else 'other'
    return (f'V923_WINDOWS_SCHEDULER_RETURN exit={kind} scheduler_entry={int(before)} '
            f'scheduler_return={int(ok)} disable_restore={int(ok)} rfi=0 boot_verified=0',ok)

def diagnostic(line:bytes)->bool:
    return type(line) is bytes and prior_diag(line)
