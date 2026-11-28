#!/usr/bin/env python3
"""Windows complete-image original wireless setter EXI write and ABI return.

Requires a previously authenticated original SI callback, system time,
wireless branch, and native wrapper. When its ID is changed, original
EXILock/Select/Imm/Sync/Deselect/Unlock run against the explicit native
EXI host controller and SRAM endpoint. A full 44-byte write must finish.
When unchanged, the original wireless wrapper may simply return.
Never conflate an EXI lock entry with a successful transaction, nor a
wireless setter return with the SI callback or handler returning.
"""
from __future__ import annotations

import re

from audit_v848_wireless_wrapper import WRAPPER_RETURN
from audit_v862_wireless_write import (
    RETURN, FAULT_WRITE, FAULT_EXT, inspect as audit_wireless_write,
)
from windows_wireless_wrapper_v760 import (
    inspect as inspect_wrapper, diagnostic as prior,
)
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('wireless write log contract')
    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows)
            if re.fullmatch(WRAPPER_RETURN, line)]
    wrapper_ok = write_ok = False
    ordinal = changed = transfers = bytes_written = visits = polls = mmio = 0

    if len(hits) == 1:
        pos = hits[0]
        before, tail = rows[:pos + 1], rows[pos + 1:]
        if not any(line.startswith(b'V861_') for line in before):
            _, wrapper_ok = inspect_wrapper(b'\n'.join(before) + b'\n', 0)
        if wrapper_ok and rc == 0 and not timed_out:
            wrapper_fields = re.fullmatch(WRAPPER_RETURN, rows[pos])
            ordinal, changed, _, _, returned, lock = (
                int(v) for v in wrapper_fields.groups())
            if ((not changed and returned == 1 and lock == 0 and len(tail) == 0)
                    or (changed and ordinal == 3 and returned == 0 and lock == 1
                        and len(tail) == 1 and re.fullmatch(RETURN, tail[0]))):
                _, write_ok = audit_wireless_write(raw, rc)
                if write_ok and changed:
                    match = re.fullmatch(RETURN, tail[0])
                    visits, polls, mmio = (int(v) for v in match.groups())
                    transfers, bytes_written = 12, 44

    ok = bool(wrapper_ok and write_ok and rc == 0 and not timed_out)
    if not ok:
        ordinal = changed = transfers = bytes_written = visits = polls = mmio = 0
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V761_WINDOWS_WIRELESS_WRITE exit={exit_kind} '
        f'wrapper_verified={int(wrapper_ok)} write_verified={int(ok)} '
        f'ordinal={ordinal} changed={changed} '
        f'transfers={transfers} bytes={bytes_written} '
        f'visits={visits} polls={polls} mmio={mmio} '
        f'original_unlock={int(ok and changed == 1)} '
        'callback_return=0 handler_return=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or re.fullmatch(RETURN, line) is not None or
        re.fullmatch(FAULT_WRITE, line) is not None or
        re.fullmatch(FAULT_EXT, line) is not None
    )
