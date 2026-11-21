#!/usr/bin/env python3
"""Categorize actual generated native C++ harness assertions without leaking data.

The earlier original-free source-only catalog has different string positions
from the owner-run generated harness after source transformations. Never use
a numeric index from one catalog to index another. Compare the exact public
diagnostic messages inside the ephemeral generated public harness instead.
Only a fixed enum is disclosed; never raw exception or game-derived code.
"""
import argparse
from pathlib import Path
from classify_v38_native_failure import STRING, ERROR

LABELS={
    "V95 duplicate allocator wrapper":"v95_duplicate",
    "V95 ES open cleanup missing":"v95_cleanup",
    "V190 original Wii rescheduler failed to reach real second IOS successor":"v190_successor",
    "V190 original Wii rescheduler did not retain second IOS IPC state":"v190_state",
    "V94 original ES request cleanup missing":"v94_cleanup",
}

def classify(source: str, private_log: str)->str:
    allowed=set(STRING.findall(source))
    candidates=ERROR.findall(private_log)
    if not candidates:
        return "none"
    for candidate in candidates:
        if candidate not in allowed:
            continue
        return LABELS.get(candidate,"other")
    return "unknown"

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("public_generated_harness",type=Path)
    a=p.parse_args()
    kind=classify(a.public_generated_harness.read_text(encoding="utf-8"),
                  a.private_native_log.read_text(encoding="utf-8",errors="replace"))
    print(f"V190_OWNER_GUARD kind={kind}")
