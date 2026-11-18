#!/usr/bin/env python3
import sys
from pathlib import Path
codes={"ValueError: V73 original sleep edge differs":770,
"ValueError: V73 original sleep return differs":771,
"ValueError: V68 range not uniquely mapped":772,
"ValueError: V68 overlap with inherited text":773}
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
print(f"V67_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
