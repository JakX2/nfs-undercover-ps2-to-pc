#!/usr/bin/env python3
"""Report only public source-owned error categories."""
import sys
from pathlib import Path
codes={
"ValueError: V70 authentic STM call graph differs":740,
"ValueError: V70 original OSInit alternate target differs":741,
"ValueError: V70 STM original return differs":742,
"ValueError: V68 range not uniquely mapped":743,
"ValueError: V68 overlap with inherited text":744,
}
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
print(f"V67_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
