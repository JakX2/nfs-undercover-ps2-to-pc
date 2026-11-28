#!/usr/bin/env python3
"""Strict complete-original Windows native RFI and pending-SI reentry audit.

This mode does not accept a pre-RFI hook as proof. It requires the already
verified full-image V920 handler return, V921 original saved frame, original
V922 scheduler/loader RFI state transition, and V932 real second-vector
entry in one Windows native process, with native rc=0.
"""
from __future__ import annotations

import re
from windows_startup_scope_v434 import MAX_LOG
from windows_handler_return_v763 import inspect as predecessor,diagnostic as diag_handler
from audit_v920_handler_return import RETURN as HANDLER_RETURN

JOIN=(b'WINDOWS_RFI_CONTEXT_JOIN original_snapshot=1 original_handler_return=1 '
      b'saved_gprs=32 special=6 same_cpu=1 rfi=0 boot_verified=0')
SOURCE=b'V932_PENDING_SOURCE held_completion=1 only_si=1'
FIRST=b'V922_IRQ_RETURN_STAGE n=1'
SECOND=b'V922_IRQ_RETURN_STAGE n=2'
RFI=b'V932_RFI_REENTRY restored_integer=1 native_rfi=1 second_exception=1 same_tick=1'
POLL=b'V932_REENTRY_POLL same_tick=1 no_guest_instruction=1'
RESULT=re.compile(
    rb'V932_REENTRY_RESULT native_rfi=1 second_exception=1 '
    rb'vector_entry=1 restored_context=1 visits=([1-9][0-9]{0,2}) '
    rb'device_held=1 resumed_instruction_executed=0 boot_verified=0')
FAULT=re.compile(rb'V922_IRQ_RETURN_INVALID kind=[1-8] reason=[0-9]{1,3} '
                 rb'stage=[0-5] visits=[0-9]{1,3}')
BEGIN_FAULT=re.compile(rb'V932_IRQ_BEGIN_REFUSAL mask=[0-9]{1,3}')
RELATED=(b'WINDOWS_RFI_CONTEXT_JOIN',b'V922_',b'V932_')


def inspect(raw:bytes,rc:int,timed_out:bool=False)->tuple[str,bool]:
    if (type(raw) is not bytes or len(raw)>MAX_LOG or type(rc) is not int or
            type(timed_out) is not bool):
        raise ValueError('Windows original RFI result contract')
    rows=raw.splitlines()
    hits=[i for i,line in enumerate(rows) if line==HANDLER_RETURN]
    handler=False;joined=False;returned=False;visits=0
    if len(hits)==1 and not timed_out:
        i=hits[0]
        prefix=b'\n'.join(rows[:i+1])+b'\n'
        _,handler=predecessor(prefix,0)
        if handler and not any(line.startswith(RELATED) for line in rows[:i]):
            tail=rows[i+1:]
            scoped=[line for line in tail if line.startswith(RELATED)]
            match=RESULT.fullmatch(scoped[-1]) if scoped else None
            expected=[JOIN,SOURCE,FIRST,SECOND,RFI,POLL]
            joined=bool(match and scoped[:-1]==expected and
                        tail and tail[-1]==scoped[-1] and
                        1<=int(match[1])<=512)
            returned=bool(joined and rc==0)
            if returned:visits=int(match[1])
    reason='timeout' if timed_out else 'zero' if rc==0 else 'exception' if rc<0 or rc>=0xC0000000 else 'other'
    return (
        f'V926_WINDOWS_ORIGINAL_RFI exit={reason} handler_return={int(handler)} '
        f'saved_context={int(joined)} native_rfi={int(returned)} '
        f'second_vector={int(returned)} visits={visits} '
        'original_resume_executed=0 boot_verified=0',
        returned,
    )


def diagnostic(line:bytes)->bool:
    return type(line) is bytes and bool(
        diag_handler(line) or FAULT.fullmatch(line) or BEGIN_FAULT.fullmatch(line))
