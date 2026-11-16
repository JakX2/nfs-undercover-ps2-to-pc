#!/usr/bin/env python3
"""Fail-closed validation of original-free cloud Ghidra call-graph smoke output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LANGUAGE = "PowerPC:BE:32:Gekko_Broadway"
START = "0x8000403C"
HELPER = "0x80004050"


def validate(payload: dict) -> None:
    if payload.get("schema") != "uc-wii-function-index-v1":
        raise ValueError("unexpected Ghidra index schema")
    if payload.get("language") != LANGUAGE:
        raise ValueError("Ghidra did not load the Broadway PowerPC language")
    funcs = payload.get("functions")
    if not isinstance(funcs, list):
        raise ValueError("missing discovered functions")
    by_pc = {f["pc"]: f for f in funcs}
    if not {START, HELPER}.issubset(by_pc):
        raise ValueError("synthetic PPC start/helper function discovery failed")
    if HELPER not in by_pc[START].get("calls", []):
        raise ValueError("synthetic original-free PowerPC branch/link not analyzed as a call")
    if any(not isinstance(f.get("size"), int) or f["size"] <= 0 for f in funcs):
        raise ValueError("invalid function sizes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    validate(json.loads(args.manifest.read_text(encoding="utf-8")))
    print("PASS: Ghidra GameCube/Wii DOL loader, PowerPC functions and callgraph verified")


if __name__ == "__main__":
    main()
