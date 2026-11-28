#!/usr/bin/env python3
"""Windows complete-image fourth SI transfer return, not handler return.

Require the full V742 predecessor plus V777 native device handoff and
original ABI return. Never accept a busy-lane return as MMIO execution.
Raw owner logs and instruction data are kept private.
"""
from __future__ import annotations
import re
from audit_v742_handler_time import RESULT as TIME_RESULT, diagnostic as time_diagnostic
from audit_v777_transfer_return import ENTRY, HANDOFF, RESULT, PREFIX, inspect as audit_return
from windows_startup_scope_v434 import MAX_LOG, audit as audit_time


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('transfer return log contract')
    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows) if re.fullmatch(TIME_RESULT, line)]
    time_ok = False
    return_ok = False
    idle = reads = writes = follow = pending = 0
    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(l.startswith(PREFIX + (b'V747_',)) for l in before):
            _, time_ok = audit_time(b'\n'.join(before) + b'\n', 0,
                                    'os-si-handler-time')
        match = re.fullmatch(RESULT, tail[2]) if len(tail) == 3 else None
        if (time_ok and len(tail) == 3 and re.fullmatch(ENTRY, tail[0]) and
                tail[1] == HANDOFF and match and rc == 0 and not timed_out):
            _, return_ok = audit_return(raw, rc)
            if return_ok:
                idle, _, reads, writes, follow, pending, _ = map(int, match.groups())
    ok = bool(return_ok)
    return (
        'V752_WINDOWS_TRANSFER_RETURN exit=' +
        ('timeout' if timed_out else
         'zero' if rc == 0 else
         'exception' if rc < 0 or rc >= 0xC0000000 else 'other') +
        f' time_verified={int(time_ok)} transfer_return_verified={int(ok)}'
        f' idle={idle} reads={reads} writes={writes} follow={follow} pending={pending}'
        ' handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        time_diagnostic(line) or re.fullmatch(ENTRY, line) is not None or
        line == HANDOFF or re.fullmatch(RESULT, line) is not None or
        re.fullmatch(
            rb'V777_TRANSFER_INVALID kind=[1-7] reason=[0-8] stage=[0-4]'
            rb' visits=[0-9]{1,3} device=[0-9] follow=[0-6] trace=[0-9]{1,2}'
            rb'|V777_TRANSFER_MMIO_INVALID kind=[12] reason=[0-9]', line) is not None
    )
