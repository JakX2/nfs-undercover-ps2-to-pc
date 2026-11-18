#!/usr/bin/env python3
import sys
from pathlib import Path
codes={"ValueError: V74 original scheduler edge differs":780,
"ValueError: V74 original scheduler return differs":781,
"ValueError: V68 range not uniquely mapped":782,
"ValueError: V68 overlap with inherited text":783}
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
print(f"V67_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
