#!/usr/bin/env python3
"""Emit only fixed public categories for private V71 fixture fabrication errors."""
import sys
from pathlib import Path
codes={
"ValueError: V71 original IOS_Open call edge changed":750,
"ValueError: V71 original IOS_Open return geometry changed":751,
"ValueError: V71 original allocator tail differs":752,
"ValueError: V71 original allocator return differs":756,
"ValueError: V71 original allocator IRQ edge differs":757,
"ValueError: V68 range not uniquely mapped":753,
"ValueError: V68 overlap with inherited text":754,
"ValueError: V68 replacement geometry":755,
}
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
print(f"V67_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
