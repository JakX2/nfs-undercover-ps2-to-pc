#!/usr/bin/env python3
import sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
codes={f"ValueError: V67 private fixture range {i} {kind}":700+3*i+j for i in range(5) for j,kind in enumerate(("not mapped","overlap","return"))}
codes.update({f"ValueError: {msg}":code for code,msg in ((730,"V67 original arena call graph changed"),(731,"V67 inherited data count changed"),(732,"V67 original entry changed"))})
print(f"V67_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
