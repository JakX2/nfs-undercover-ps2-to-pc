#!/usr/bin/env python3
"""Windows complete-image original callback system-time return.

AOT execution must first authenticate the genuine SI transfer and alarm
return, enter the original callback, execute its compiler save, then run
its original OS system-time leaf and return to the callback. Stop before
a later callback call/return, handler BLR, game main or any rendered frame.
"""
from __future__ import annotations

import re

from audit_v809_callback_prefix import DONE as CALLBACK_DONE
from audit_v822_callback_time import (
    TIME_ENTRY, TIME_RETURN, TIME_FAULT, inspect as audit_callback_time,
)
from windows_callback_prefix_v756 import (
    inspect as inspect_callback_prefix, diagnostic as prior,
)
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('callback time log contract')
    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows)
            if re.fullmatch(CALLBACK_DONE, line)]
    callback_ok = time_ok = False
    ordinal = polls = reads = leaf_visits = 0

    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(line.startswith(b'V813_') for line in before):
            _, callback_ok = inspect_callback_prefix(
                b'\n'.join(before) + b'\n', 0)
        if (callback_ok and rc == 0 and not timed_out and
                len(tail) == 2 and tail[0] == TIME_ENTRY):
            match = re.fullmatch(TIME_RETURN, tail[1])
            if match:
                _, time_ok = audit_callback_time(raw, rc)
                if time_ok:
                    leaf_visits, polls, reads = map(int, match.groups())
                    # The prior callback prefix is independently checked.
                    begin = next((line for line in before
                                  if line.startswith(b'V807_CALLBACK_ENTRY ')), b'')
                    match_entry = re.fullmatch(
                        rb'V807_CALLBACK_ENTRY ordinal=([0-9]{1,2}) identity=1 follow=3',
                        begin)
                    if match_entry:
                        ordinal = int(match_entry[1])
                    else:
                        time_ok = False

    ok = bool(callback_ok and time_ok and rc == 0 and not timed_out)
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V758_WINDOWS_CALLBACK_TIME exit={exit_kind} '
        f'callback_prefix_verified={int(callback_ok)} time_return_verified={int(ok)} '
        f'ordinal={ordinal if ok else 0} leaf_visits={leaf_visits if ok else 0} '
        f'polls={polls if ok else 0} reads={reads if ok else 0} '
        'callback_return=0 handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or line == TIME_ENTRY or
        re.fullmatch(TIME_RETURN, line) is not None or
        re.fullmatch(TIME_FAULT, line) is not None
    )
