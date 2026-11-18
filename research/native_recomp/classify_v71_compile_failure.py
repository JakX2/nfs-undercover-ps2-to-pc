#!/usr/bin/env python3
"""Classify compiler failures without leaking source or raw diagnostics."""
import re,sys
from pathlib import Path
from classify_v67_compile_failure import classify
log=Path(sys.argv[1]).read_text(errors="replace")
unit=sys.argv[2]
assert unit in ("harness","generated","loader")
print(f"V67_NATIVE_ASSERTION id={classify(log):03d}")
print(f"V71_COMPILE_UNIT {unit}")
# Strict allowlist: public harness location or standard compiler warning name.
for line in log.splitlines():
    if "error:" not in line:continue
    m=re.search(r"test_start_to_ios_open_v71\.cpp:(\d+):\d+: (?:fatal )?error:",line)
    if unit=="harness" and m:print("V71_HARNESS_LINE "+m.group(1))
    m=re.search(r"\[-Werror=([a-z0-9-]+)\]",line)
    if m and m.group(1) in ("parentheses","misleading-indentation","unused-but-set-variable",
        "unused-function","unused-parameter","unused-variable","sign-compare","return-type",
        "maybe-uninitialized","uninitialized","array-bounds","stringop-overflow","overflow",
        "implicit-fallthrough","type-limits","narrowing","address","format","strict-aliasing",
        "sequence-point","int-in-bool-context","write-strings","missing-field-initializers"):
        print("V71_WARNING "+m.group(1))
    break
