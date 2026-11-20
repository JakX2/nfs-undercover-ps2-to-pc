#!/usr/bin/env python3
"""Audit only original-free V177/V178 C++ harness around V77's ACK fallback.

No game executable, translated PPC code, owner fixture, private file, network
access or arbitrary traceback content is opened. Printed source originates
solely from independently authored, public test_start_to_ipc_ack_v77.cpp.
"""
from pathlib import Path
from derive_v177_sc_reply_next_harness import derive as v177
from derive_v178_sc_reply_burst_harness import derive as v178

HERE=Path(__file__).resolve().parent
NEEDLE='check(false,"unexpected original IPC ACK-only path dependency");'
MAX_ROW=155
PRE_ROWS=76

def public_window(source: str, tag: str)->list[str]:
    rows=source.splitlines()
    hits=[i for i,row in enumerate(rows) if NEEDLE in row]
    if len(hits)!=1:
        raise ValueError(f"V178 public fallback count differs in {tag}: {len(hits)}")
    idx=hits[0]
    lo=max(0,idx-PRE_ROWS)
    lines=[f"V178_PUBLIC_GUARD {tag} line={idx+1}"]
    for n in range(lo, min(idx+3,len(rows))):
        line=rows[n].rstrip()
        lines.append(f"V178_GUARD_{tag.upper()} {n+1} {line[:MAX_ROW]}")
    return lines

def main()->None:
    base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
    before=v177(base)
    after=v178(base)
    for row in public_window(before,"before")+public_window(after,"after"):
        print(row)

if __name__=="__main__":
    main()
