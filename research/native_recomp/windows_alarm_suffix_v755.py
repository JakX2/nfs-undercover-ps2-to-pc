#!/usr/bin/env python3
"""Windows complete-image SI caller frontier after original fifth alarm return.

The earlier V754 audit must pass unchanged. The only admitted continuation
is the native V789 classifier immediately before the next original linked
call or handler BLR. Neither target nor return instruction executes here.
"""
from __future__ import annotations

import re

from audit_v747_time_suffix import CONTROL, INVALID
from audit_v778_transfer_suffix import BOUNDARY, BLR
from audit_v786_alarm_return import RESULT as ALARM_RESULT
from audit_v789_alarm_suffix import CLASS, inspect as audit_suffix
from windows_alarm_return_v754 import inspect as inspect_alarm, diagnostic as prior
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('alarm suffix log contract')

    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows)
            if re.fullmatch(ALARM_RESULT, line)]
    alarm_ok = boundary_ok = False
    ordinal = kind = target = follow = blr = 0

    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(line.startswith(b'V789_') for line in before):
            _, alarm_ok = inspect_alarm(b'\n'.join(before) + b'\n', 0)
        boundary = (
            rc == 126 and len(tail) == 4 and
            all(re.fullmatch(pattern, line) is not None
                for pattern, line in zip(
                    (CONTROL, CLASS, BOUNDARY, INVALID), tail))
        )
        terminal = rc == 0 and len(tail) == 1 and (
            re.fullmatch(BLR, tail[0]) is not None)
        if alarm_ok and not timed_out and (boundary or terminal):
            _, boundary_ok = audit_suffix(raw, rc)
            if boundary_ok and boundary:
                ordinal, kind, target = map(int, re.fullmatch(CLASS, tail[1]).groups())
                follow = int(re.fullmatch(BOUNDARY, tail[2])[5])
            elif boundary_ok and terminal:
                follow = int(re.fullmatch(BLR, tail[0])[3])
                blr = 1

    ok = bool(alarm_ok and boundary_ok and not timed_out)
    return (
        'V755_WINDOWS_ALARM_SUFFIX '
        f'alarm_return_verified={int(alarm_ok)} suffix_verified={int(ok)} '
        f'ordinal={ordinal} kind={kind} target_class={target} '
        f'follow={follow} blr_boundary={blr} '
        'target_executed=0 handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or any(
            re.fullmatch(pat, line) is not None
            for pat in (CONTROL, CLASS, BOUNDARY, INVALID, BLR)
        )
    )
