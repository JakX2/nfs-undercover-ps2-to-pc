#!/usr/bin/env python3
"""Public address allowlist for link errors; never print private symbols/logs."""
import re,sys
from pathlib import Path
from classify_v67_compile_failure import classify
log=Path(sys.argv[1]).read_text(errors="replace")
# All these addresses are already published in the original-free fixture guards.
allowed={0x8051ad38:960,0x8051ab34:961,0x80519944:962,0x805195ec:963,
         0x805222c0:964,0x805265ac:965,0x805265d4:966,0x8052b034:967,0x8051a1a4:968}
found=set()
for line in log.splitlines():
    if "undefined reference" not in line:continue
    for name in re.findall(r"func_([0-9a-fA-F]{8})",line):
        found.add(allowed.get(int(name,16),969))
if not found:found.add(classify(log))
for code in sorted(found):print(f"V67_NATIVE_ASSERTION id={code:03d}")
