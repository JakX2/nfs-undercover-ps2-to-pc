#!/usr/bin/env python3
"""Accept a verified alarm return plus the next refused linked call or BLR.

No indirect target, BLR, context restoration or boot is claimed executed.
"""
import argparse
import re
from pathlib import Path
from audit_v786_alarm_return import inspect as alarm, START, RESULT
from audit_v777_transfer_return import PREFIX, ENTRY, HANDOFF, RESULT as TRANSFER
from audit_v742_handler_time import diagnostic as prior, MAX_LOG
from audit_v778_transfer_suffix import BOUNDARY, BLR
from audit_v747_time_suffix import CONTROL, INVALID

CLASS = rb'V789_ALARM_BOUNDARY ordinal=([6-9]|1[0-2]) kind=([12]) target_class=([0-4]) executed=0'
PREFIXES = PREFIX + (b'V786_', b'V789_', b'V778_', b'V726_HANDLER_', b'V747_NEXT_')


def inspect(raw, rc):
    if len(raw) > MAX_LOG or not 0 <= rc <= 255:
        raise ValueError('geometry')
    rows = raw.splitlines()
    hits = [i for i, line in enumerate(rows) if re.fullmatch(RESULT, line)]
    ok = False
    ordinal = kind = target = follow = 0
    blr = False
    if len(hits) == 1:
        i = hits[0]
        _, valid = alarm(b'\n'.join(rows[:i + 1]), 0)
        old = int(re.fullmatch(RESULT, rows[i])[7])
        tail = [l for l in rows[i + 1:] if l.startswith(PREFIXES)]
        def held(f):
            return old == f == 0 or old == 2 and f in (2, 3) or old == f == 3
        if valid and rc == 126 and len(tail) == 4:
            a, b, c, d = (re.fullmatch(p, l) for p, l in zip(
                (CONTROL, CLASS, BOUNDARY, INVALID), tail))
            if a and b and c and d:
                ordinal, kind, target = map(int, b.groups())
                v, p, follow = map(int, c.groups()[2:])
                ok = bool(a.groups()[:2] == b.groups()[:2] == c.groups()[:2] and
                          c.groups()[2:4] == d.groups() and p <= v <= 1024 and
                          held(follow) and
                          (kind == 1 and a[3] == b'18' and target == 0 or
                           kind == 2 and a[3] == b'19' and ordinal in (6, 11)
                           and 1 <= target <= 4))
        elif valid and rc == 0 and len(tail) == 1:
            b = re.fullmatch(BLR, tail[0])
            if b:
                v, p, follow = map(int, b.groups())
                ok = bool(p <= v <= 1024 and held(follow))
                blr = ok
    return (f'V789_ALARM_SUFFIX_CENSUS rc={rc} original_alarm_return={int(ok)} '
            f'next_ordinal={ordinal if ok else 0} next_kind={kind if ok else 0} '
            f'target_class={target if ok else 0} follow={follow if ok else 0} '
            f'blr_boundary={int(blr)} verified={int(ok)} boot_verified=0'), ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument('log', type=Path)
    p.add_argument('rc', type=int)
    a = p.parse_args()
    try:
        if a.log.stat().st_size > MAX_LOG:
            raise ValueError('size')
        raw = a.log.read_bytes()
        row, ok = inspect(raw, a.rc)
    except (OSError, ValueError):
        print('V789_ALARM_SUFFIX_AUDIT inspected=0')
        return 1
    for l in raw.splitlines():
        if prior(l) or l == HANDOFF or any(re.fullmatch(p, l) for p in (
                ENTRY, TRANSFER, START, RESULT, CONTROL, CLASS, BOUNDARY, INVALID, BLR,
                rb'V786_ALARM_INVALID kind=[1-5] route=[0-8] queue=[0-5] mismatch=[0-6] device=[0-7] stage=[0-4] visits=[0-9]{1,3}')):
            print(l.decode())
    print(row)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
