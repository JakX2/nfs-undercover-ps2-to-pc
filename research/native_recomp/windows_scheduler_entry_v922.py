#!/usr/bin/env python3
"""Strict Windows first original scheduler call proof following native handler return."""
from __future__ import annotations
import re
from windows_handler_return_v763 import inspect as previous, diagnostic as prior_diag
from audit_v920_handler_return import RETURN as HANDLER_RETURN
from windows_startup_scope_v434 import MAX_LOG

RESULT=(b'V922_SCHEDULER_ENTRY original_handler_return=1 original_dispatcher_branch=1 '
        b'original_scheduler_entry=1 native_tick=1 rfi=0 boot_verified=0')

def inspect(raw:bytes,rc:int,timed_out:bool=False)->tuple[str,bool]:
    if type(raw) is not bytes or len(raw)>MAX_LOG or type(rc) is not int or type(timed_out) is not bool:
        raise ValueError('scheduler log contract')
    rows=raw.splitlines();matches=[i for i,line in enumerate(rows) if line==HANDLER_RETURN]
    handler=False
    if len(matches)==1 and not timed_out:
        prefix=b'\n'.join(rows[:matches[0]+1])+b'\n'
        _,handler=previous(prefix,0)
    ok=bool(handler and rc==0 and not timed_out and rows[matches[0]+1:]==[RESULT])
    kind='timeout' if timed_out else 'zero' if rc==0 else 'exception' if rc<0 or rc>=0xC0000000 else 'other'
    return (f'V922_WINDOWS_SCHEDULER exit={kind} handler_return={int(handler)} '
            f'scheduler_entry={int(ok)} native_tick={int(ok)} rfi=0 boot_verified=0',ok)

def diagnostic(line:bytes)->bool:
    if type(line) is not bytes:return False
    return bool(prior_diag(line) or re.fullmatch(
        rb'V922_WINDOWS_SCHEDULER_INVALID reason=(?:[1-9]|1[0-7])',line))
