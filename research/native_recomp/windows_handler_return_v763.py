#!/usr/bin/env python3
"""Windows complete-image proof of original SI handler return after callback.

The original V868/V919/V920 witnesses are reused; earlier valid stops are
diagnostics, never handler-return progress. No RFI, main, or boot claim.
"""
from __future__ import annotations

import re
from audit_v852_callback_return import CALLBACK_RETURN
from audit_v870_handler_suffix import inspect as audit_suffix, BAD as SUFFIX_FAULT
from audit_v920_handler_return import inspect as audit_return, RETURN as HANDLER_RETURN
from windows_combined_callback_v762 import inspect_completed as callback_return, diagnostic as prior
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('handler return log contract')
    rows = raw.splitlines()
    markers = [i for i, line in enumerate(rows)
               if re.fullmatch(CALLBACK_RETURN, line)]
    callback_ok = suffix_ok = handler_ok = False
    if len(markers) == 1 and rc == 0 and not timed_out:
        prefix = b'\n'.join(rows[:markers[0] + 1]) + b'\n'
        _, callback_ok = callback_return(prefix, 0)
        if callback_ok:
            suffix_row, suffix_observed, _ = audit_suffix(raw, 0)
            suffix_ok = bool(suffix_observed and
                             'handler_continuation=1' in suffix_row and
                             'handler_ordinal=6 next=12 kind=1 ' in suffix_row)
            if suffix_ok:
                _, handler_ok = audit_return(raw, 0)
    # Native V920 prints this exact terminal marker and exits immediately.
    # Reject anything appended after it, including otherwise unrecognized
    # output that the shared diagnostic auditors intentionally ignore.
    ok = bool(callback_ok and suffix_ok and handler_ok and
              rows and rows[-1] == HANDLER_RETURN)
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V763_WINDOWS_HANDLER exit={exit_kind} '
        f'callback_return={int(callback_ok)} handler_suffix={int(suffix_ok)} '
        f'handler_return={int(ok)} rfi=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or re.fullmatch(SUFFIX_FAULT, line) is not None
    )
