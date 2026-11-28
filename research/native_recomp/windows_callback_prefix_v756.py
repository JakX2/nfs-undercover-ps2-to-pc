#!/usr/bin/env python3
"""Windows complete-image original SI callback prologue and compiler save.

Requires the complete original fifth-call alarm return, then an exact
authenticated bctrl entry into the original callback. The first
post-save instruction remains unexecuted. Never claim callback return,
handler return, game main, first frame or gameplay.
"""
from __future__ import annotations

import re

from audit_v786_alarm_return import RESULT as ALARM_RESULT
from audit_v809_callback_prefix import BEGIN, DONE, FAULT, inspect as audit_callback
from windows_alarm_return_v754 import inspect as inspect_alarm, diagnostic as prior
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('callback prefix log contract')

    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows)
            if re.fullmatch(ALARM_RESULT, line)]
    alarm_ok = callback_ok = False
    ordinal = 0

    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(line.startswith((b'V807_', b'V789_')) for line in before):
            _, alarm_ok = inspect_alarm(b'\n'.join(before) + b'\n', 0)
        if (alarm_ok and rc == 0 and not timed_out and len(tail) == 2 and
                re.fullmatch(BEGIN, tail[0]) and
                re.fullmatch(DONE, tail[1])):
            _, callback_ok = audit_callback(raw, rc)
            if callback_ok:
                ordinal = int(re.fullmatch(BEGIN, tail[0])[1])

    ok = bool(alarm_ok and callback_ok and rc == 0 and not timed_out)
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V756_WINDOWS_CALLBACK_PREFIX exit={exit_kind} '
        f'alarm_return_verified={int(alarm_ok)} callback_prefix_verified={int(ok)} '
        f'ordinal={ordinal} original_prologue={int(ok)} compiler_save={int(ok)} '
        'continuation_executed=0 callback_return=0 handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or re.fullmatch(BEGIN, line) is not None or
        re.fullmatch(DONE, line) is not None or
        re.fullmatch(FAULT, line) is not None
    )
