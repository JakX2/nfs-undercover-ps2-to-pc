#!/usr/bin/env python3
"""Windows full-image original SI callback suffix/ABI return.

Bind the original V861 profile-backed SRAM write (or the authentic
unchanged wireless route) to V850 compiler restore and dispatcher return.
The callback can instead stop at an unadmitted original call or an
ordinal-5 getter. Accept and report these *different* outcomes explicitly;
none proves that the SI handler returned, IRQ RFI executed or main ran.
"""
from __future__ import annotations

import re

from audit_v848_wireless_wrapper import WRAPPER_RETURN
from audit_v862_wireless_write import RETURN as WRITE_RETURN
from audit_v852_callback_return import (
    SUFFIX_ENTRY, SUFFIX_RETURN, CALLBACK_RETURN, CALLBACK_FAULT,
)
from audit_v864_combined_callback import inspect as audit_combined
from windows_wireless_write_v761 import (
    inspect as inspect_write, diagnostic as prior,
)
from windows_startup_scope_v434 import MAX_LOG


def inspect(raw: bytes, rc: int, timed_out: bool = False) -> tuple[str, bool]:
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(rc) is not int or type(timed_out) is not bool):
        raise ValueError('combined callback log contract')
    rows = raw.splitlines()
    markers = [i for i, line in enumerate(rows)
               if re.fullmatch(WRAPPER_RETURN, line)]
    write_ok = combined_ok = False
    ordinal = handler = boundary = suffix_visits = callback_return = changed = 0

    if len(markers) == 1:
        pos = markers[0]
        wrapper = re.fullmatch(WRAPPER_RETURN, rows[pos])
        ordinal, changed, _, _, _, _ = (int(x) for x in wrapper.groups())
        write_indices = [i for i, line in enumerate(rows)
                         if re.fullmatch(WRITE_RETURN, line)]
        if (len(write_indices) == int(bool(changed)) and
                (not changed or write_indices[0] > pos)):
            last = write_indices[0] if changed else pos
            before, tail = rows[:last + 1], rows[last + 1:]
            if not any(line.startswith(b'V850_') for line in before):
                _, write_ok = inspect_write(b'\n'.join(before) + b'\n', 0)
            valid_tail = False
            if ordinal == 5 and not changed and not tail:
                valid_tail = True
            elif ordinal == 3 and len(tail) in (2, 3):
                entry = re.fullmatch(SUFFIX_ENTRY, tail[0])
                suffix = re.fullmatch(SUFFIX_RETURN, tail[1])
                if entry and suffix:
                    boundary = int(suffix[1])
                    suffix_visits = int(suffix[3])
                    handler = int(entry[1])
                    if boundary == 4 and len(tail) == 2:
                        valid_tail = True
                    elif boundary == 13 and len(tail) == 3:
                        returned = re.fullmatch(CALLBACK_RETURN, tail[2])
                        valid_tail = bool(returned and int(returned[1]) == handler)
                        callback_return = int(valid_tail)
            if write_ok and valid_tail and rc == 0 and not timed_out:
                _, combined_ok = audit_combined(raw, rc)

    ok = bool(write_ok and combined_ok and rc == 0 and not timed_out)
    if not ok:
        ordinal = handler = boundary = suffix_visits = callback_return = changed = 0
    exit_kind = ('timeout' if timed_out else
                 'zero' if rc == 0 else
                 'exception' if rc < 0 or rc >= 0xC0000000 else 'other')
    return (
        f'V762_WINDOWS_COMBINED_CALLBACK exit={exit_kind} '
        f'write_verified={int(write_ok)} continuation_verified={int(ok)} '
        f'handler_ordinal={handler} wireless_ordinal={ordinal} changed={changed} '
        f'suffix_boundary={boundary} suffix_visits={suffix_visits} '
        f'callback_return={callback_return} outer_dispatch={callback_return} '
        'handler_return=0 rfi=0 boot_verified=0',
        ok,
    )


def diagnostic(line: bytes) -> bool:
    return type(line) is bytes and (
        prior(line) or re.fullmatch(SUFFIX_ENTRY, line) is not None or
        re.fullmatch(SUFFIX_RETURN, line) is not None or
        re.fullmatch(CALLBACK_RETURN, line) is not None or
        re.fullmatch(CALLBACK_FAULT, line) is not None
    )
