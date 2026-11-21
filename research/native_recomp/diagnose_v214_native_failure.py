#!/usr/bin/env python3
"""Classify private-native failures using the *compiled* public C++ harness.

An ID from classify_v67_native_failure.py is relative to the exact
temporary harness.cpp, so a separate re-derivation may shift IDs.
Read owner-native log only inside CI and print bounded categories.
Never print the raw exception, pathname, guest memory or binaries.
"""
import argparse
import re
from pathlib import Path
from classify_v38_native_failure import ERROR, STRING

TRIAL=re.compile(r"^V79_TRIAL_PASS trial=(?:[0-9]|1[0-5])$",re.MULTILINE)
NEGATIVE=re.compile(
    r"^V214_Y2_NEGATIVE invalid=[01] mode=[01] path=[01] published=[01] "
    r"irq=[01] drained=[01] cpu=[01] sc=[01]$",re.MULTILINE
)
KNOWN={
    "V82 scheduler did not set default thread context":"v82_context",
    "V82 second IRQ scheduler ABI differs":"v82_scheduler",
    "V82 original RFI did not restore default thread":"v82_rfi",
    "V208 second IOS opened file descriptor kind differs":"v208_open",
    "V214 original second IOS_Open negative reply was not faithfully published":"v214_negative",
    "V183 second original IPC request pointer or phase invalid":"v183_ipc",
}

def diagnose(private_log:str, actual_public_harness:str)->str:
    public=set(STRING.findall(actual_public_harness))
    failures=[s for s in ERROR.findall(private_log) if s in public]
    kind=KNOWN.get(failures[0],"other_public") if failures else "unmatched"
    trials=min(16,len(TRIAL.findall(private_log)))
    neg=min(16,len(NEGATIVE.findall(private_log)))
    return f"V214_NATIVE_DIAG public={int(bool(failures))} kind={kind} trials={trials} negative={neg}"

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    p.add_argument("actual_public_harness",type=Path)
    a=p.parse_args()
    print(diagnose(
        a.private_native_log.read_text(encoding="utf-8",errors="replace"),
        a.actual_public_harness.read_text(encoding="utf-8",errors="replace")))
