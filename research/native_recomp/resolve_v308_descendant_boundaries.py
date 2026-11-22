#!/usr/bin/env python3
"""V308: classify exact, interior, and absent ELF function boundaries.

A direct bl target may point into an STT_FUNC, not to its first byte.
Never manufacture a whole-function size from such a target. Return only
the bounded, authenticated function-tail window for interior targets.
Unmapped and ambiguous targets get no original coverage claim.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_FUNCTION_BYTES = 32768

@dataclass(frozen=True)
class Window:
    kind: str
    entry: int
    offset: int
    length: int

def valid(entry: int, length: int) -> bool:
    return (0x80000000 <= entry < 0x94000000 and entry%4 == 0 and
            4 <= length <= MAX_FUNCTION_BYTES and length%4 == 0 and
            entry+length <= 0x94000000)

def resolve(functions: dict[int,int], target: int) -> Window:
    if target%4 or not 0x80000000 <= target < 0x94000000:
        raise ValueError("invalid_target")
    exact=functions.get(target)
    if exact is not None:
        if valid(target,exact):
            return Window("exact",target,0,exact)
        return Window("invalid",0,0,0)
    parents=[
        (entry,size) for entry,size in functions.items()
        if valid(entry,size) and entry < target < entry+size
    ]
    if len(parents)==1:
        entry,size=parents[0]
        return Window("interior",entry,target-entry,entry+size-target)
    if len(parents)>1:
        return Window("ambiguous",0,0,0)
    return Window("unknown",0,0,0)
