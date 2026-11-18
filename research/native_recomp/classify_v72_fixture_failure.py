#!/usr/bin/env python3
import sys
from pathlib import Path
codes={"ValueError: V72 original submission edge differs":760,
"ValueError: V72 original submission return differs":761,
"ValueError: V68 range not uniquely mapped":762,
"ValueError: V68 overlap with inherited text":763}
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
print(f"V67_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
