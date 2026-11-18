#!/usr/bin/env python3
"""Fixed public failure IDs. Never emit private fixture strings."""
import sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
codes={f"ValueError: V66 private fixture range {i} {kind}":700+3*i+j for i in range(6) for j,kind in enumerate(("not mapped","overlap","return"))}
codes.update({f"ValueError: {msg}":code for code,msg in (
(730,"V66 original boot report call edge changed"),(731,"V66 original boot report extension overlaps inherited text"),
(732,"V66 inherited data count changed"),(733,"V66 original console jump table geometry changed"),
(734,"V66 original version pointer differs"),(735,"V66 original entry changed"))})
print(f"V66_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
