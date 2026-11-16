#!/usr/bin/env python3
"""Validate a private Ghidra result without revealing or publishing its contents."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ADDRESS = re.compile(r"0x[0-9A-F]{8}\Z")
START = "0x8000403C"


def validate(payload: dict, minimum: int = 1000) -> tuple[int, int]:
    if payload.get("schema") != "uc-wii-function-index-v1":
        raise ValueError("incorrect function-manifest schema")
    if payload.get("language") != "PowerPC:BE:32:Gekko_Broadway":
        raise ValueError("incorrect Wii PowerPC language")
    funcs = payload.get("functions")
    if not isinstance(funcs, list) or len(funcs) < minimum:
        raise ValueError("too few original function candidates")
    seen = set()
    call_count = 0
    for f in funcs:
        if not isinstance(f, dict) or not isinstance(f.get("pc"), str) or not ADDRESS.fullmatch(f["pc"]):
            raise ValueError("invalid function address")
        if f["pc"] in seen:
            raise ValueError("duplicated function address")
        seen.add(f["pc"])
        if type(f.get("size")) is not int or f["size"] <= 0:
            raise ValueError("invalid function size")
        calls = f.get("calls")
        if not isinstance(calls, list) or any(not isinstance(c, str) or not ADDRESS.fullmatch(c) for c in calls):
            raise ValueError("invalid function call targets")
        call_count += len(calls)
    if START not in seen:
        raise ValueError("original Wii entry point not discovered")
    if call_count == 0:
        raise ValueError("no direct or resolved calls discovered")
    return len(funcs), call_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    count, calls = validate(json.loads(args.manifest.read_text(encoding="utf-8")))
    print(f"PASS: private Ghidra Broadway function analysis: functions={count}, resolved_edges={calls}")
    # Do not include address lists, names, or code bytes in logs or artifacts.


if __name__ == "__main__":
    main()
