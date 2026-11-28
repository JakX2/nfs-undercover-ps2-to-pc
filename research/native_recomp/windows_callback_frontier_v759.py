#!/usr/bin/env python3
"""Windows complete-image original callback to the wireless-service callsite.

This step executes the original callback continuation after the system
time helper returns, then stops at the original wireless-service callsite
without executing that callee, EXI activity or the callback epilogue.
"""
from __future__ import annotations

import re

from audit_v822_callback_time import TIME_RETURN
from audit_v836_callback_frontier import (
    FRONTIER_ENTRY, FRONTIER_RETURN, FRONTIER_FAULT,
    inspect as audit_callback_frontier,
)
from windows_callback_time_v758 import (
    inspect as inspect_callback_time, diagnostic as prior,
)
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('callback frontier log contract')
    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows)
            if re.fullmatch(TIME_RETURN, line)]
    time_ok = frontier_ok = False
    ordinal = visits = writes = zero = 0

    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(line.startswith(b'V831_') for line in before):
            _, time_ok = inspect_callback_time(b'\n'.join(before) + b'\n', 0)
        if (time_ok and rc == 0 and not timed_out and
                len(tail) == 2 and tail[0] == FRONTIER_ENTRY):
            match = re.fullmatch(FRONTIER_RETURN, tail[1])
            if match:
                _, frontier_ok = audit_callback_frontier(raw, rc)
                if frontier_ok:
                    ordinal, visits, writes, zero = map(int, match.groups())

    ok = bool(time_ok and frontier_ok and rc == 0 and not timed_out)
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V759_WINDOWS_CALLBACK_FRONTIER exit={exit_kind} '
        f'time_return_verified={int(time_ok)} frontier_verified={int(ok)} '
        f'wireless_ordinal={ordinal if ok else 0} visits={visits if ok else 0} '
        f'writes={writes if ok else 0} zero_id={zero if ok else 0} '
        'wireless_executed=0 callback_return=0 handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or line == FRONTIER_ENTRY or
        re.fullmatch(FRONTIER_RETURN, line) is not None or
        re.fullmatch(FRONTIER_FAULT, line) is not None
    )
