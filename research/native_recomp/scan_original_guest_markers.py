#!/usr/bin/env python3
"""Read private original AOT logs, retaining only exact capped public markers.

Unlike head/tail sampling, this preserves a marker pair from the omitted
middle of a private log. Raw guest bytes, words and paths are never emitted.
Overflow or an overlarge file must fail closed.
"""
from __future__ import annotations
from pathlib import Path
import re

MAX_ORIGINAL_LOG_BYTES=8_000_000
MAX_GUEST_MARKER_LENGTH=240
MAX_PER_PATTERN=16

def scan_original_guest_markers(path:Path,
    patterns:tuple[re.Pattern[str],...],
    per_pattern:int=MAX_PER_PATTERN
    )->tuple[int,list[str],bool]:
    if not patterns or not 1<=per_pattern<=16:
        raise ValueError("invalid_bounded_marker_request")
    size=path.stat().st_size
    if size>MAX_ORIGINAL_LOG_BYTES:
        return size,[],True
    found:list[str]=[]
    counts=[0]*len(patterns)
    overflow=False
    with path.open("rb") as stream:
        for raw in stream:
            if len(raw)>MAX_GUEST_MARKER_LENGTH:
                continue
            try:line=raw.decode("ascii").rstrip("\r\n")
            except UnicodeDecodeError:continue
            for i,pattern in enumerate(patterns):
                if not pattern.fullmatch(line):continue
                if counts[i]>=per_pattern:overflow=True
                else:
                    counts[i]+=1
                    found.append(line)
                break
    return size,found,overflow
