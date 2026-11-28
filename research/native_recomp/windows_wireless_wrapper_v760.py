#!/usr/bin/env python3
"""Windows full-image original SI callback through wireless wrapper.

Continue after genuine original time helper and callback wireless callsite.
Observe the unmodified original wireless wrapper's branch, guest writes,
and return, or stop at the *entry* to its genuine EXI lock on the changed
lane. No EXI transaction, setter return, callback return, handler RFI,
game main, first frame or boot is claimed.
"""
from __future__ import annotations

import re

from audit_v836_callback_frontier import FRONTIER_RETURN
from audit_v848_wireless_wrapper import (
    WRAPPER_ENTRY, WRAPPER_RETURN, WRAPPER_FAULT,
    inspect as audit_wireless,
)
from windows_callback_frontier_v759 import (
    inspect as inspect_frontier, diagnostic as prior,
)
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('wireless wrapper log contract')

    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows)
            if re.fullmatch(FRONTIER_RETURN, line)]
    frontier_ok = wireless_ok = False
    ordinal = changed = visits = writes = returned = lock = 0

    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(line.startswith(b'V847_') for line in before):
            _, frontier_ok = inspect_frontier(
                b'\n'.join(before) + b'\n', 0)
        if frontier_ok and rc == 0 and not timed_out and len(tail) == 2:
            begin = re.fullmatch(WRAPPER_ENTRY, tail[0])
            result = re.fullmatch(WRAPPER_RETURN, tail[1])
            if begin and result:
                _, wireless_ok = audit_wireless(raw, rc)
                if wireless_ok:
                    ordinal, changed, visits, writes, returned, lock = (
                        int(v) for v in result.groups())

    ok = bool(frontier_ok and wireless_ok and rc == 0 and not timed_out)
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V760_WINDOWS_WIRELESS_WRAPPER exit={exit_kind} '
        f'frontier_verified={int(frontier_ok)} wrapper_verified={int(ok)} '
        f'ordinal={ordinal if ok else 0} changed={changed if ok else 0} '
        f'visits={visits if ok else 0} writes={writes if ok else 0} '
        f'original_return={returned if ok else 0} exilock_entry={lock if ok else 0} '
        'exi_executed=0 callback_return=0 handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or re.fullmatch(WRAPPER_ENTRY, line) is not None or
        re.fullmatch(WRAPPER_RETURN, line) is not None or
        re.fullmatch(WRAPPER_FAULT, line) is not None
    )
