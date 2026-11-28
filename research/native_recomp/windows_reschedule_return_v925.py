#!/usr/bin/env python3
"""Strict complete-image reschedule return, before original context loader."""
from __future__ import annotations
from windows_reschedule_entry_v924 import inspect as earlier,RESULT as PREDECESSOR,diagnostic as diag
from windows_startup_scope_v434 import MAX_LOG

RESULT=(b'V925_WINDOWS_RESCHEDULE_RETURN scheduler_return=1 original_reschedule_return=1 '
        b'original_dispatcher_resume=1 no_thread_switch=1 abi=1 context_loader_executed=0 '
        b'rfi=0 boot_verified=0')

def inspect(raw:bytes,rc:int,timed_out:bool=False)->tuple[str,bool]:
    if type(raw) is not bytes or len(raw)>MAX_LOG or type(rc) is not int or type(timed_out) is not bool:
        raise ValueError('reschedule return contract')
    rows=raw.splitlines();matches=[i for i,line in enumerate(rows) if line==PREDECESSOR]
    returned=False
    if len(matches)==1 and rc==0 and not timed_out:
        prefix=b'\n'.join(rows[:matches[0]+1])+b'\n'
        _,returned=earlier(prefix,0)
    ok=bool(returned and rows[matches[0]+1:]==[RESULT])
    kind='timeout' if timed_out else 'zero' if rc==0 else 'exception' if rc<0 or rc>=0xC0000000 else 'other'
    return (f'V925_WINDOWS_RESCHEDULE_RETURN exit={kind} reschedule_entry={int(returned)} '
            f'reschedule_return={int(ok)} no_thread_switch={int(ok)} rfi=0 boot_verified=0',ok)

def diagnostic(line:bytes)->bool:
    return type(line) is bytes and diag(line)
