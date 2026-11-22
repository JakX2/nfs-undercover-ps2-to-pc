#!/usr/bin/env python3
"""Classify real Wii IPC/interrupt state at an unchanged 64-call guest frontier.

Only compact aggregates leave private CI. No raw game instructions, memory
bytes, or proprietary translated code are exposed by this analyzer.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import sys

SAMPLES=64
TRIALS=16
PATTERN=re.compile(
    r'^V262_STATE n=([1-9]|[1-5][0-9]|6[0-4]) mapped=([01]) '
    r'ee=([01]) irq=([01]) native_request=([01]) '
    r'queued=([0-9]{1,3}) sc=([0-9]{1,3}) reply=([01])$'
)

@dataclass(frozen=True)
class State:
    mapped: int
    ee: int
    irq: int
    request: int
    queued: int
    sc: int
    reply: int


def parse(log: str) -> list[tuple[State, ...]]:
    trials=[]
    current=[]
    for line in log.splitlines():
        if not line.startswith('V262_STATE '):
            continue
        match=PATTERN.fullmatch(line)
        if match is None:
            raise ValueError('malformed_state_marker')
        n,mapped,ee,irq,request,queued,sc,reply=map(int,match.groups())
        if n!=len(current)+1:
            raise ValueError('out_of_order_state')
        if not mapped:
            raise ValueError('unmapped_sc_state')
        current.append(State(mapped,ee,irq,request,queued,sc,reply))
        if len(current)==SAMPLES:
            if current[-1].sc!=1:
                raise ValueError('frontier_sc_changed')
            trials.append(tuple(current))
            current=[]
    if current:
        raise ValueError('incomplete_state_window')
    if len(trials)!=TRIALS:
        raise ValueError('trial_count_changed')
    return trials


def count_edges(seq:tuple[State,...],name:str)->int:
    return sum(getattr(seq[i],name)!=getattr(seq[i-1],name)
               for i in range(1,len(seq)))


def summary(trials:list[tuple[State,...]])->str:
    if len(trials)!=TRIALS:
        raise ValueError('trial_count_changed')
    def signature(seq):
        raw=bytes(x for s in seq for x in
                  (s.mapped,s.ee,s.irq,s.request,s.queued&255,s.sc,s.reply))
        return hashlib.sha256(raw).hexdigest()[:16]
    distinct=len({signature(seq) for seq in trials})
    seq=trials[0]
    return (
        f'V262_IPC_STATE trials={TRIALS} calls={SAMPLES} '
        f'stable={int(distinct==1)} distinct={distinct} '
        f'ee_edges={count_edges(seq,"ee")} irq_edges={count_edges(seq,"irq")} '
        f'request_edges={count_edges(seq,"request")} '
        f'queue_edges={count_edges(seq,"queued")} '
        f'sc_edges={count_edges(seq,"sc")} '
        f'irq_ever={int(any(s.irq for s in seq))} '
        f'request_ever={int(any(s.request for s in seq))} '
        f'queue_max={max(s.queued for s in seq)} '
        f'reply_all={int(all(s.reply for s in seq))} '
        f'sc_first={seq[0].sc} sc_last={seq[-1].sc} '
        f'digest={signature(seq)}'
    )


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_log',type=Path)
    a=p.parse_args()
    try:
        print(summary(parse(a.private_log.read_text(encoding='utf-8',errors='replace'))))
    except (OSError,ValueError) as exc:
        reason=str(exc)
        if reason not in {'malformed_state_marker','out_of_order_state',
                          'unmapped_sc_state','frontier_sc_changed',
                          'incomplete_state_window','trial_count_changed'}:
            reason='input_error'
        print(f'V262_STATE_ERROR reason={reason}',file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    sys.exit(main())
