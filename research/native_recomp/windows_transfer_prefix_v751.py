#!/usr/bin/env python3
"""Windows full-image original SI transfer prefix, stopping before MMIO.

Reuse the authenticated V742 time return and the existing V768 original
transfer prefix. This is not a complete SI transaction or game boot.
"""
from __future__ import annotations
import re
from typing import NamedTuple
from audit_v742_handler_time import RESULT as TIME_RESULT, diagnostic as time_diagnostic
from audit_v768_transfer_prefix import (
    ENTRY, RESULT, inspect as audit_transfer,
)
from windows_startup_scope_v434 import MAX_LOG, audit as audit_time


class TransferPlan(NamedTuple):
    env: dict[str, str]
    analyzer: tuple[str, ...]
    observers: tuple[tuple[str, str], ...]


def plan(scope: str, synthetic: bool, prefix: bool, time_suffix: bool,
         returned: bool = False) -> TransferPlan:
    """One contract for source ownership, observer order and launch flags."""
    if any(type(x) is not bool for x in (synthetic, prefix, time_suffix, returned)):
        raise ValueError('transfer option')
    if not prefix and not returned:
        return TransferPlan({}, (), ())
    if synthetic or scope != 'os-si-handler-time' or time_suffix or (prefix and returned):
        raise ValueError('transfer scope')
    # Match the existing Linux full-image translation contract. The
    # analyzer owns the original transfer root and compiler save alias;
    # V777 also needs the authenticated compiler restore alias.
    analyzer = ('--transfer-prefix',)
    observers = (('transfer_prefix_observer', 'prepare_v768_transfer_prefix.py'),)
    env = {'UNDERCOVER_V747_TIME_SUFFIX': '1'}
    if returned:
        analyzer += ('--transfer-return',)
        observers += (('transfer_return_observer', 'prepare_v777_transfer_return.py'),)
        env['UNDERCOVER_V777_TRANSFER_RETURN'] = '1'
    else:
        env['UNDERCOVER_V768_TRANSFER_PREFIX'] = '1'
    return TransferPlan(env, analyzer, observers)


def launch_overlay(scope: str, synthetic: bool, enabled: bool,
                   time_suffix: bool) -> dict[str, str]:
    """Compatibility wrapper for the independent prefix-only contract."""
    return plan(scope, synthetic, enabled, time_suffix).env


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
        # disables interrupts, then stops before the next unadmitted call or MMIO.
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
