#!/usr/bin/env python3
"""V118 derives original async IOS control-register read call boundary."""
import argparse
from pathlib import Path
from derive_v117_sc_send_register_runner import derive as previous

EDITS = [
 ("derive_v117_sc_send_register_harness.py","derive_v118_sc_async_mailbox_harness.py"),
 ("V117_TRIAL_PASS","V118_TRIAL_PASS"),
 ("V117 recovered continuous original __start->SC IOS queue-helper return and IPC send-register entry assertions",
  "V118 recovered continuous original __start->SC IOS control-register read entry assertions"),
 ("stop=0x8051906c","stop=0x8051905c"),
 ("V117_STAGE native_test_passed","V118_STAGE native_test_passed"),
 ("V117_NATIVE_EXIT","V118_NATIVE_EXIT"),
 ("BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=117",
  "BOOT_PROGRESS entry=0x8000403C pc=0x8051905C stage=118"),
]

def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:
            raise ValueError("V118 runner missing source anchor: "+a)
        s=s.replace(a,b)
    mark="echo 'V118_STAGE native_test_passed'"
    if s.count(mark)!=1:
        raise ValueError("V118 runner pass marker absent/ambiguous")
    return s.replace(mark,mark+"""
grep -E '^V118_CTRL_READ_ENTRY route=1 abi=1 prior=1 msg=[01]$' "$log" """.rstrip())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))

if __name__=="__main__":
    main()
