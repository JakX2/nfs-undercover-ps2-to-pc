#!/usr/bin/env python3
"""V294: regenerate, syntax-compile and link owner-private restored NAND AOT.

Inherited V293 verifies 16 authentic baseline trials and 195 restored
PowerPC words without executing restored functions. This stage compiles
an entirely separate candidate binary, checks coverage and link
success, but does NOT execute unverified newly restored code.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
HERE=Path(__file__).resolve().parent
DONE="echo 'V293_PRIVATE_RESTORE verified=1'"
EXTRA=r'''
# Independently regenerate the authenticated restored candidate.
mkdir "$work/generated-v294"
if "$work/generator" "$work/private-v293.dol" "$work/generated-v294" owner \
    > "$work/v294-generation.log" 2>&1; then
  echo 'V294_AOT_STAGE regenerate=1'
else
  echo 'V294_AOT_STAGE regenerate=0'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/audit_v292_nand_aot_reach.py" \
     "$owner" "$work/private-v293.dol" "$work/generated-v294/output.cpp" \
      > "$work/v294-aot-audit.log" 2>&1; then
  echo 'V294_AOT_STAGE inspect=1'
else
  grep -Fx 'V292_AOT_AUDIT verified=0' "$work/v294-aot-audit.log" || true
  echo 'V294_AOT_STAGE inspect=0'
  exit 1
fi
cat "$work/v294-aot-audit.log"
if python3 "$V110_SOURCE_ROOT/analyze_v294_restored_aot.py" \
     "$work/v294-aot-audit.log" > "$work/v294-coverage.log" 2>&1; then
  cat "$work/v294-coverage.log"
  echo 'V294_AOT_STAGE coverage=1'
else
  grep -E '^V294_COVERAGE_AUDIT verified=0$|^V294_AOT_COVERAGE targets=4 ' "$work/v294-coverage.log" || true
  echo 'V294_AOT_STAGE coverage=0'
  exit 1
fi
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
       -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include" \
       -c "$work/generated-v294/output.cpp" -o "$work/v294-generated.o" \
       > "$work/v294-compile.log" 2>&1; then
  echo 'V294_AOT_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py" \
    "$work/v294-compile.log" generated || true
  echo 'V294_AOT_STAGE compile=0'
  exit 1
fi
if g++ "$work/v250-harness.o" "$work/v294-generated.o" "$work/loader.o" \
       -o "$work/v294-native" > "$work/v294-link.log" 2>&1; then
  test -s "$work/v294-native"
  test -x "$work/v294-native"
  echo 'V294_AOT_STAGE link=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v71_link_failure.py" \
    "$work/v294-link.log" || true
  echo 'V294_AOT_STAGE link=0'
  exit 1
fi
echo 'V294_RESTORED_AOT verified=1'
'''
def patch(source):
    if source.count(DONE)!=1:raise ValueError("V293 generator seam changed")
    return source.replace(DONE,DONE+"\n"+EXTRA,1)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v294-") as td:
        temp=Path(td)/"v293.sh"
        proc=subprocess.run(
            [sys.executable,str(HERE/"derive_v293_private_nand_restore_runner.py"),
             str(a.source),str(temp)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if proc.returncode:raise ValueError("V294 previous private generator failed")
        with a.output.open("x",encoding="utf-8") as stream:
            stream.write(patch(temp.read_text(encoding="utf-8")))
    return 0
if __name__=="__main__":
    sys.exit(main())
