#!/usr/bin/env python3
"""Private SHA-verified original Wii retry-edge classification; aggregate only."""
import argparse
import hashlib
from pathlib import Path
from audit_v264_osinit_retry_elf import CALLSITE, HELPER, read_words
from make_private_elf_symbol_map import ORIGINAL_SHA256, parse_functions
from ppc_retry_edge import classify_retry_window, sanitized

def audit(data: bytes) -> dict[str, int]:
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise ValueError("digest")
    functions = parse_functions(data)
    if len(functions) < 25000 or HELPER not in functions:
        raise ValueError("symbols")
    owners = [(pc, size) for pc, size in functions.items()
              if pc <= CALLSITE < pc + size and 0x80400000 <= pc < 0x80600000]
    if len(owners) != 1:
        raise ValueError("caller")
    start, size = owners[0]
    if size < 32 or size > 32768 or size % 4:
        raise ValueError("geometry")
    window_start = CALLSITE - 24
    window_end = CALLSITE + 4 * 65
    if window_start < start or window_end > start + size:
        raise ValueError("geometry")
    words = read_words(data, window_start, (window_end - window_start) // 4)
    return classify_retry_window(window_start, words, CALLSITE)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner_elf", type=Path)
    args = parser.parse_args()
    try:
        stats = audit(args.owner_elf.read_bytes())
    except (OSError, ValueError):
        print("RETRY_EDGE_AUDIT verified=0")
        return 1
    print("RETRY_EDGE_AUDIT verified=1")
    print(sanitized(stats))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
