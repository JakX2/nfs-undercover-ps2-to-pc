#!/usr/bin/env python3
"""Only fixed source-owned failure codes are emitted from private construction."""
import sys
from pathlib import Path
codes={f"ValueError: {message} {i}":700+10*j+i
       for j,message in enumerate(("V69 original IPC function return differs","V69 IPC text not uniquely mapped",
                                    "V69 original IPC overlaps previous code"))
       for i in range(10)}
codes.update({"ValueError: V69 FPR segment missing":730,
              "ValueError: V69 IPC text extension overlaps earlier text":731,
              "ValueError: V69 original IPC edge changed":732,
              "ValueError: V68 overlap with inherited text":733,
              "ValueError: V68 range not uniquely mapped":734,
              "ValueError: V69 original entry changed":735})
lines=Path(sys.argv[1]).read_text(errors="replace").splitlines()
print(f"V67_NATIVE_ASSERTION id={next((codes[line] for line in reversed(lines) if line in codes),799):03d}")
