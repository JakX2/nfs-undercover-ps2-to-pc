#!/usr/bin/env python3
"""Bounded compiler-failure classifier for the original-free V238 harness.

Only a whitelisted declaration category, compiler failure type and
source line are printed. Owner game code, private diagnostic text,
register contents and source excerpts are never printed or uploaded.
"""
import argparse
import re
from pathlib import Path

ERROR = re.compile(
    r"(?m)^.*(?:harness|test_start_to_ipc_ack_v77)\.cpp:"
    r"([0-9]{1,6}):(?:[0-9]{1,5}:)?\s*(?:fatal )?error:\s*([^\r\n]{1,340})"
)
KINDS = (
    ("duplicate", re.compile(r"redeclaration|redefinition|conflicting declaration")),
    ("undeclared", re.compile(r"was not declared|not declared in this scope")),
    ("member", re.compile(r"is not a member|has no member")),
    ("conversion", re.compile(r"cannot convert|invalid conversion")),
    ("expected", re.compile(r"expected|before.*token")),
    ("other", re.compile(r".")),
)
QUOTED = re.compile(r"['\u2018]([A-Za-z_][A-Za-z_0-9]{0,63})['\u2019]")
DECLS = {
    "sp", "caller", "nand", "logging", "other", "r11", "mode",
    "srcmode", "nandcb", "pathptr", "chars", "pathmapped",
    "terminated", "validpath", "sysconf", "mapped", "seq",
    "v238_save_count", "v238_source_seen", "v238_second_mode",
    "v238_second_modevalid", "v238_second_r11", "ctx", "v237_counts"
}

def diagnose(log: str) -> str:
    m = ERROR.search(log)
    if not m:
        return "V238_COMPILE_DIAG found=0 kind=none symbol=other line=0"
    line = min(999999, int(m.group(1)))
    detail = m.group(2)
    kind = next((name for name, pattern in KINDS if pattern.search(detail)), "other")
    quoted = QUOTED.findall(detail)
    symbol = next((name for name in quoted if name in DECLS), "other")
    return (f"V238_COMPILE_DIAG found=1 kind={kind} "
            f"symbol={symbol} line={line}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_compile_log", type=Path)
    a = p.parse_args()
    print(diagnose(a.private_compile_log.read_text(
        encoding="utf-8", errors="replace")))
