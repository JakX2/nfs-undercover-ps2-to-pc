#!/usr/bin/env python3
"""Fixed public error categories only. Never emit private fixture strings."""
import sys
from pathlib import Path
log=Path(sys.argv[1]).read_text(errors="replace")
lines=log.splitlines()
codes={f"ValueError: V65 private fixture range {i} {kind}":700+2*i+j for i in range(11) for j,kind in enumerate(("not mapped","overlap"))}
codes.update({f"ValueError: {msg}":code for code,msg in (
(730,"V65 original memory protection call edge changed"),(731,"original BAT trampoline rfi changed"),
(732,"V65 original shutdown registration data changed"),(733,"V65 inherited data count differs"),
(734,"V65 original entry changed"))})
code=next((codes[line] for line in reversed(lines) if line in codes),799)
print(f"V65_NATIVE_ASSERTION id={code:03d}")
