#!/usr/bin/env python3
"""Strict, redacted Windows full-image check for the first post-time call.

The existing V742 Windows scope must remain independently valid. A V747
expected refusal is a *verified boundary*, never a successful handler
return, first frame or boot. No owner instruction data is emitted.
"""
from __future__ import annotations

import re

from audit_v742_handler_time import RESULT as TIME_RESULT
from audit_v747_time_suffix import (
    BOUNDARY, CONTROL, INVALID, inspect as inspect_suffix,
    diagnostic as suffix_diagnostic,
)
from windows_startup_scope_v434 import (
    MAX_LOG, PREFIXES, FAILURE_PREFIXES, audit as inspect_time,
)


def launch_overlay(scope: str, synthetic: bool, enabled: bool) -> dict[str, str]:
    """Fail closed unless explicitly requested for an original time scope."""
    if type(enabled) is not bool or type(synthetic) is not bool:
        raise ValueError('suffix option')
    if not enabled:
        return {}
    if synthetic or scope != 'os-si-handler-time':
        raise ValueError('suffix scope')
    return {'UNDERCOVER_V747_TIME_SUFFIX': '1'}


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    """Require a separately valid V742 prefix and exact V747 refusal.

    Exit 126 is *only* accepted with the authenticated control, boundary
    and refusal triple. All unrelated original-scope failures remain
    failures even if a forged suffix triple is appended.
    """
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('suffix log contract')
    rows = raw.splitlines()
    result_positions = [i for i, line in enumerate(rows)
                        if re.fullmatch(TIME_RESULT, line)]
    time_ok = False
    suffix_ok = False
    tail_ok = False
    if len(result_positions) == 1:
        cut = result_positions[0]
        before, after = rows[:cut + 1], rows[cut + 1:]
        # No V747 marker is permissible before the authenticated time
        # return, including a marker ignored by V434's older whitelist.
        if not any(line.startswith(b'V747_') for line in before):
            _, time_ok = inspect_time(b'\n'.join(before) + b'\n', 0,
                                      'os-si-handler-time')
        # The failure at the final guarded call is deliberately expected.
        # All other hardware/SDK failures and scope-family events after
        # the time return must be rejected, never silently dropped.
        # The production observer emits the invalid-call record then
        # _Exit(126); accepting arbitrary output after it would conceal
        # unbounded execution beyond the guard.
        tail_ok = bool(after and re.fullmatch(INVALID, after[-1])) and all(
            (not line.startswith(FAILURE_PREFIXES) or
             re.fullmatch(INVALID, line) is not None) and
            (not line.startswith(PREFIXES) or
             re.fullmatch(CONTROL, line) is not None or
             re.fullmatch(INVALID, line) is not None) and
            (not line.startswith(b'V747_') or
             re.fullmatch(BOUNDARY, line) is not None)
            for line in after
        )
        if rc == 126 and not timed_out and time_ok and tail_ok:
            _, suffix_ok = inspect_suffix(raw, rc)
    ok = bool(time_ok and tail_ok and suffix_ok and
              rc == 126 and not timed_out)
    return (
        'V750_WINDOWS_SUFFIX exit=' +
        ('timeout' if timed_out else
         'expected_refusal' if rc == 126 else
         'zero' if rc == 0 else
         'exception' if rc < 0 or rc >= 0xC0000000 else 'other') +
        f' time_verified={int(time_ok)} boundary_verified={int(ok)}'
        ' handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and suffix_diagnostic(line) is True
