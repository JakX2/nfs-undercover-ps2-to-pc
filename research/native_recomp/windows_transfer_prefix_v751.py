#!/usr/bin/env python3
"""Windows full-image original SI transfer prefix, stopping before MMIO.

Reuse the authenticated V742 time return and the existing V768 original
transfer prefix. This is not a complete SI transaction or game boot.
"""
from __future__ import annotations
import re
from audit_v742_handler_time import RESULT as TIME_RESULT, diagnostic as time_diagnostic
from audit_v768_transfer_prefix import (
    ENTRY, RESULT, inspect as audit_transfer,
)
from windows_startup_scope_v434 import MAX_LOG, audit as audit_time


def launch_overlay(scope: str, synthetic: bool, enabled: bool,
                   time_suffix: bool) -> dict[str, str]:
    if any(type(x) is not bool for x in (synthetic, enabled, time_suffix)):
        raise ValueError('transfer option')
    if not enabled:
        return {}
    if synthetic or scope != 'os-si-handler-time' or time_suffix:
        raise ValueError('transfer scope')
    # The V742 observer exits immediately after system time unless the
    # already existing V747 continuation flag is set.
    return {'UNDERCOVER_V747_TIME_SUFFIX': '1',
            'UNDERCOVER_V768_TRANSFER_PREFIX': '1'}


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('transfer log contract')
    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows) if re.fullmatch(TIME_RESULT, line)]
    time_ok = False
    tail_ok = False
    transfer_ok = False
    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(l.startswith(b'V768_') for l in before):
            _, time_ok = audit_time(b'\n'.join(before) + b'\n', 0,
                                    'os-si-handler-time')
        # The guest reaches the original transfer prologue, saves GPRs,
        # disables interrupts, then stops at the guarded first MMIO.
        # Nothing else is permitted after the authenticated time return.
        tail_ok = (len(tail) == 2 and
                   re.fullmatch(ENTRY, tail[0]) is not None and
                   re.fullmatch(RESULT, tail[1]) is not None)
        if time_ok and tail_ok and rc == 0 and not timed_out:
            _, transfer_ok = audit_transfer(raw, rc)
    ok = bool(time_ok and tail_ok and transfer_ok and
              rc == 0 and not timed_out)
    return (
        'V751_WINDOWS_TRANSFER exit=' +
        ('timeout' if timed_out else
         'zero' if rc == 0 else
         'exception' if rc < 0 or rc >= 0xC0000000 else 'other') +
        f' time_verified={int(time_ok)} transfer_prefix_verified={int(ok)}'
        ' mmio_executed=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        time_diagnostic(line) or re.fullmatch(ENTRY, line) is not None or
        re.fullmatch(RESULT, line) is not None or
        re.fullmatch(
            rb'V768_TRANSFER_INVALID kind=[1-6] reason=[0-7] stage=[0-3]'
            rb' visits=[0-9]{1,3} trace=[0-9]{1,2}', line) is not None
    )
