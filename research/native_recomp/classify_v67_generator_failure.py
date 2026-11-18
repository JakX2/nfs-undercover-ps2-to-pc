#!/usr/bin/env python3
"""Report only a numeric index of a public generator assertion. No owner log output."""
import re,sys
from pathlib import Path
from classify_v38_native_failure import STRING
def classify(source,log):
    messages=sorted(set(STRING.findall(source)))
    prefixes=("V25 generator: ","V67 generator: ")
    for line in log.splitlines():
        if line.startswith(prefixes):
            actual=line.split(": ",1)[1]
            for i,expected in enumerate(messages,1):
                if actual==expected or (expected.endswith(": ") and actual.startswith(expected)):
                    return i if i<900 else 999
    return 999
if __name__=="__main__":
    print(f"V67_NATIVE_ASSERTION id={classify(Path(sys.argv[2]).read_text(),Path(sys.argv[1]).read_text(errors='replace')):03d}")
