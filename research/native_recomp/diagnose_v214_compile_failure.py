#!/usr/bin/env python3
"""Bounded compiler diagnostic for public V214 native harness.

Private compilations can contain original translated code. Parse only
compiler error *types* and bounded public harness line, never print raw
compiler output or file contents.
"""
from pathlib import Path
import argparse
import re

ERROR=re.compile(r"(?m)^.*(?:harness|test_start_to_ipc_ack_v77)\.cpp:([0-9]{1,6}):(?:[0-9]{1,5}:)?\s*(?:fatal )?error:\s*([^\r\n]{1,320})")
KIND=(
    ("duplicate",re.compile(r"(?:redeclaration|redefinition|conflicting declaration)")),
    ("undeclared",re.compile(r"(?:was not declared|has not been declared|not declared in this scope)")),
    ("member",re.compile(r"(?:is not a member of|has no member named|no member named)")),
    ("unused",re.compile(r"(?:unused|set but not used)")),
    ("conversion",re.compile(r"(?:cannot convert|invalid conversion|could not convert)")),
    ("expected",re.compile(r"(?:expected|before.*token|does not name a type)")),
    ("call",re.compile(r"(?:no matching function|no match for|candidate expects)")),
    ("ambiguous",re.compile(r"ambiguous")),
)
IDENTIFIERS={
    "v214_negative_seen":"v214_state",
    "invalid_fd":"invalid_fd",
    "publication":"publication",
    "bad_mode":"bad_mode",
    "nonzero_path":"nonzero_path",
}
SINGLE_QUOTE=re.compile(r"[‘'\\u2018\\u2019]([A-Za-z_][A-Za-z_0-9]{1,64})[’'\\u2018\\u2019]")

def diagnose(log:str,unit:str)->str:
    if unit not in ("harness","generated","loader","generator"):
        raise ValueError("unexpected compilation unit")
    m=ERROR.search(log)
    if not m:
        return f"V214_COMPILE_DIAG unit={unit} kind=no_public_error line=0 symbol=other"
    line=min(999999,int(m.group(1)))
    reason=m.group(2)
    kind=next((name for name,pattern in KIND if pattern.search(reason)),"other")
    quoted=SINGLE_QUOTE.search(reason)
    symbol=IDENTIFIERS.get(quoted.group(1),"other") if quoted else "other"
    return f"V214_COMPILE_DIAG unit={unit} kind={kind} line={line} symbol={symbol}"

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_compile_log",type=Path)
    p.add_argument("unit",choices=("harness","generated","loader","generator"))
    args=p.parse_args()
    print(diagnose(args.private_compile_log.read_text(encoding="utf-8",errors="replace"),args.unit))
