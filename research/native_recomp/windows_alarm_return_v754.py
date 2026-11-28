#!/usr/bin/env python3
"""Windows complete-image fifth SI-handler alarm-cancellation return.

This opt-in lane composes the existing original-code V742 -> V777 ->
V778 -> V786 installers. The result is a bounded original alarm
function return, not an SI handler return, game main, or game boot.
"""
from __future__ import annotations

import re

from audit_v777_transfer_return import RESULT as TRANSFER_RESULT
from audit_v786_alarm_return import START, RESULT, inspect as audit_alarm
from windows_startup_scope_v434 import MAX_LOG
from windows_transfer_return_v752 import inspect as inspect_transfer, diagnostic as prior


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('alarm return log contract')

    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows)
            if re.fullmatch(TRANSFER_RESULT, line)]
    transfer_ok = alarm_ok = False
    lane = timer = deferred = calls = visits = polls = follow = 0

    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        # No earlier alarm or caller-suffix marker may masquerade as an
        # original fifth-call completion.
        if not any(line.startswith((b'V778_', b'V786_', b'V789_'))
                   for line in before):
            _, transfer_ok = inspect_transfer(b'\n'.join(before) + b'\n', 0)
        match = re.fullmatch(RESULT, tail[1]) if len(tail) == 2 else None
        if (transfer_ok and rc == 0 and not timed_out and
                len(tail) == 2 and re.fullmatch(START, tail[0]) and
                match):
            _, alarm_ok = audit_alarm(raw, rc)
            if alarm_ok:
                lane, timer, deferred, calls, visits, polls, follow = map(
                    int, match.groups())

    ok = bool(transfer_ok and alarm_ok and rc == 0 and not timed_out)
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V754_WINDOWS_ALARM_RETURN exit={exit_kind} '
        f'transfer_verified={int(transfer_ok)} alarm_return_verified={int(ok)} '
        f'lane={lane} timer={timer} deferred={deferred} calls={calls} '
        f'visits={visits} polls={polls} follow={follow} '
        'handler_resume=0 handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or re.fullmatch(START, line) is not None or
        re.fullmatch(RESULT, line) is not None or
        re.fullmatch(
            rb'V786_ALARM_INVALID kind=[1-5] route=[0-8] queue=[0-5]'
            rb' mismatch=[0-6] device=[0-7] stage=[0-4]'
            rb' visits=[0-9]{1,3}', line) is not None
    )
