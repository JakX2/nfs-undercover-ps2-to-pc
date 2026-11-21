#!/usr/bin/env python3
"""Bounded public-harness C++ compile error category for V215.

The owner-generated game output and native compile logs stay private.
Emit only the public harness line, compiler error kind, and recognized
public test-variable class. No raw source text or error messages.
"""
import argparse
from pathlib import Path
from diagnose_v214_compile_failure import diagnose as previous

KNOWN_SYMBOLS={
    "v215_vector_seen":"state",
    "v215_saved_pc":"state",
    "v215_saved_msr":"state",
    "v215_saved_lr":"state",
    "v215_saved_ctr":"state",
    "v215_saved_xer":"state",
    "v215_original_gprs":"state",
    "v215_ctrl":"ipc",
    "v215_flag":"ipc",
    "V215IOS":"alias",
    "V215Bus":"alias",
    "V215Mail":"alias",
    "V215Irq":"alias",
    "ctx":"context",
    "original_pc":"snapshot",
    "original_msr":"snapshot",
    "original_gprs":"snapshot",
    "v215_scheduler":"scheduler",
}
def diagnose(log:str,public_harness:str,unit:str)->str:
    summary=previous(log,unit).replace("V214_COMPILE_DIAG","V215_COMPILE_DIAG",1)
    lines=public_harness.splitlines()
    parts=summary.split(" line=")
    line=int(parts[1].split(" ",1)[0]) if len(parts)==2 else 0
    public_line=lines[line-1] if 1<=line<=len(lines) else ""
    at_code=int("v215_" in public_line or "V215_" in public_line)
    # Whitelisted type only. Never print the error's original identifier.
    import re
    m=re.search(r"(?m)^.*(?:harness|test_start_to_ipc_ack_v77)\.cpp:[0-9]{1,6}:[0-9]{1,5}: (?:fatal )?error:\s*([^\r\n]{1,320})",log)
    raw=m.group(1) if m else ""
    symbol=next((cls for key,cls in KNOWN_SYMBOLS.items()
                 if (f"'{key}'" in raw or f"‘{key}’" in raw)),"other")
    return summary+f" at_code={at_code} cls={symbol}"

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_compile_log",type=Path)
    p.add_argument("public_harness",type=Path)
    p.add_argument("unit",choices=("harness","generated","loader","generator"))
    a=p.parse_args()
    print(diagnose(
        a.private_compile_log.read_text(encoding="utf-8",errors="replace"),
        a.public_harness.read_text(encoding="utf-8",errors="replace"),
        a.unit))
