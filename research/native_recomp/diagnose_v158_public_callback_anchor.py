#!/usr/bin/env python3
"""V158 inspect bounded original-free derived callback dispatch header.

Never opens private DOLs, game fixture bytes or generated PPC translation.
Only the independently authored C++ harness from public repository is read.
"""
from pathlib import Path
from derive_v157_sc_rescheduler_next_harness import derive

base=Path(__file__).with_name("test_start_to_ipc_ack_v77.cpp")
source=derive(base.read_text(encoding="utf-8"))
needle="bool process_pending_callbacks(CPUContext& ctx){"
if source.count(needle)!=1:
    raise ValueError("V158 public callback count is not exactly one")
rest=source.split(needle,1)[1]
print("V158_PUBLIC_CALLBACK count=1")
for index,line in enumerate(rest.splitlines()[:14],1):
    print(f"V158_CALLBACK_LINE{index} {line[:140]}")
