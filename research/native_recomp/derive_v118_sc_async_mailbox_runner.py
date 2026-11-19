#!/usr/bin/env python3
"""V118 original async IOS control-read boundary with safe failure diagnostics."""
import argparse
from pathlib import Path
from derive_v117_sc_send_register_runner import derive as previous

EDITS = [
    ("derive_v117_sc_send_register_harness.py", "derive_v118_sc_async_mailbox_harness.py"),
    ("V117_TRIAL_PASS", "V118_TRIAL_PASS"),
    ("V117 recovered continuous original __start->SC IOS queue-helper return and IPC send-register entry assertions",
     "V118 recovered continuous original __start->SC IOS control-register read entry assertions"),
    ("stop=0x8051906c", "stop=0x8051905c"),
    ("V117_STAGE native_test_passed", "V118_STAGE native_test_passed"),
    ("V117_NATIVE_EXIT", "V118_NATIVE_EXIT"),
    ("BOOT_PROGRESS entry=0x8000403C pc=0x8051906C stage=117",
     "BOOT_PROGRESS entry=0x8000403C pc=0x8051905C stage=118"),
]

def derive(source):
    s = previous(source)
    for old, new in EDITS:
        if old not in s:
            raise ValueError("V118 runner missing source anchor: " + old)
        s = s.replace(old, new)
    fail_marker = "  echo 'V118_NATIVE_EXIT ok=0'"
    if s.count(fail_marker) != 1:
        raise ValueError("V118 native failure marker missing or ambiguous")
    diagnostic = (
        "  grep -E '^V118_CTRL_READ_ENTRY route=[01] abi=[01] prior=[01] msg=[0-9]{1,2}$"
        "|^V118_PPCMSG wire=[01] path=[01]$"
        "|^V118_PPCCTRL route=[01] request=[01]$"
        "|^V118_WALK seq=[0-9]{1,2} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8} msg=[0-9]{1,2} x1=[0-9]{1,2}$'"
        ' "$work/private-native.log" | sort -u || true\n'
    )
    s = s.replace(fail_marker, diagnostic + fail_marker, 1)
    stage_marker = "echo 'V118_STAGE native_test_passed'"
    if s.count(stage_marker) != 1:
        raise ValueError("V118 stage marker missing or ambiguous")
    s = s.replace(stage_marker,
                  stage_marker + '\ngrep -E \'^V118_CTRL_READ_ENTRY route=1 abi=1 prior=1 msg=[01]$\' "$log"',
                  1)
    return s

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))

if __name__ == "__main__":
    main()
