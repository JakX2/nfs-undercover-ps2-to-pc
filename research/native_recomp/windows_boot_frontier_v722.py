#!/usr/bin/env python3
"""Redacted Windows original-startup frontier, not a game boot assertion.

Only public, fixed audit markers are inspected. Never emit addresses,
instruction words, guest registers, or arbitrary owner-output lines.
The sequence is advisory; the existing V709 auditor remains authoritative.
"""
from __future__ import annotations

import re
from audit_v672_si_ack_route import RESULT
from audit_v699_si_postack import STAGE, NESTED, RETURN, END
from audit_v709_os_leaves import LEAVES, MARKERS, MAX_LOG

CHECKPOINTS = (
    (('postack', STAGE),)
    + tuple((f'nested_{i}', word) for i, word in enumerate(NESTED[:2], 1))
    + tuple((f'leaf_{i // 3 + 1}_{i % 3 + 1}', word)
            for i, word in enumerate(LEAVES))
    + (('nested_3', NESTED[2]),)
)
POLL = re.compile(rb'V719_POSTACK_LOOP_POLL n=([1-9][0-9]{0,3})\Z')


def classify_exit(rc: int, timed_out: bool) -> str:
    if type(rc) is not int or type(timed_out) is not bool:
        raise ValueError('exit contract')
    if timed_out:
        return 'timeout'
    if rc == 0:
        return 'zero'
    # Python's Windows subprocess returncode can be signed for NTSTATUS.
    if rc < 0 or rc >= 0xC0000000:
        return 'exception'
    return 'nonzero'


def frontier(raw: bytes, rc: int, timed_out: bool = False,
             scope_verified: bool = False) -> str:
    """Summarize only the first unobserved, ordered scope checkpoint.

    An observed marker is NOT proof that the underlying instruction ran
    correctly; only the separately validated owner-scope audit proves it.
    """
    if (type(raw) is not bytes or len(raw) > MAX_LOG or
            type(scope_verified) is not bool):
        raise ValueError('log contract')
    exit_kind = classify_exit(rc, timed_out)
    rows = [line for line in raw.splitlines() if line.startswith(MARKERS)]
    ack_count = rows.count(RESULT)
    last, following, reason = 'before_ack', 'postack', 'incomplete'
    complete = False
    if ack_count != 1:
        reason = 'ack_missing' if ack_count == 0 else 'ack_duplicate'
    else:
        pos = rows.index(RESULT) + 1
        tail = rows[pos:]
        k = 0
        for label, marker in CHECKPOINTS:
            if k >= len(tail):
                following = label
                break
            if tail[k] != marker:
                following, reason = label, 'unexpected'
                break
            last, k = label, k + 1
        else:
            following = 'second_return'
            n = 0
            while k < len(tail) and tail[k].startswith(b'V719_POSTACK_LOOP_POLL '):
                n += 1
                match = POL.fullmatch(tail[k])
                if not match or n > 8192 or int(match[1]) != n:
                    reason = 'poll_invalid'
                    following = 'loop_poll'
                    break
                last = 'loop_poll'
                k += 1
            else:
                for label, marker in (('second_return', RETURN),
                                      ('scope_result', END)):
                    if k >= len(tail):
                        following = label
                        break
                    if tail[k] != marker:
                        following, reason = label, 'unexpected'
                        break
                    last, k = label, k + 1
                else:
                    if k == len(tail):
                        complete = True
                        following, reason = 'none', 'scope_complete'
                    else:
                        following, reason = 'none', 'trailing'
    # A timeout is never a successful scope, even with a complete log.
    if scope_verified and (exit_kind != 'zero' or not complete):
        raise ValueError('inconsistent owner audit')
    return (f'V722_WINDOWS_FRONTIER scope=os-si-os-leaves exit={exit_kind} '
            f'last={last} next={following} reason={reason} '
            f'scope_verified={int(scope_verified)} boot_verified=0')
