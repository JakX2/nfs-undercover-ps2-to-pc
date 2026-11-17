#!/usr/bin/env python3
"""Public numeric compiler error categories only; never emit private source/log lines."""
import re,sys
from pathlib import Path

def classify(log):
    rules=(
        (901, "unused variable"),(902,"set but not used"),
        (903, "not declared in this scope"),(904,"was not declared"),
        (905, "jump to label"),(906,"crosses initialization"),
        (907, "undefined reference"),(908,"no matching function"),
        (909,"invalid conversion"),(910,"expected primary-expression"),
        (911,"not a member"),(912,"does not name a type"),
        (913,"redefinition"),(914,"conflicting declaration"),
        (915,"missing initializer"),(916,"maybe-uninitialized"),
        (917,"uninitialized"),(918,"division by zero"),
        (919,"array subscript"),(920,"shift count"),
        (921,"overflow"),(922,"comparison of integer expressions"),
        (923,"no return statement"),(924,"return-statement"),
        (925,"cannot convert"),(926,"multiple definition"),
        (927,"not used"),(928,"unrecognized command-line"),
        (929,"inconsistent deduction"),(930,"cannot bind"),
        (931,"not supported"),(932,"not found"),
        (933,"does not have"),(934,"expected"),
    )
    for line in log.splitlines():
        if not re.search(r"(?:fatal )?error:|undefined reference",line):continue
        for code,needle in rules:
            if needle in line:return code
    return 999

if __name__=="__main__":
    print(f"V56_NATIVE_ASSERTION id={classify(Path(sys.argv[1]).read_text(errors='replace')):03d}")
