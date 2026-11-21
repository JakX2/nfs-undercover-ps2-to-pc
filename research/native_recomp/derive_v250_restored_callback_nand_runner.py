#!/usr/bin/env python3
"""V250 execute restored callback AOT only to original nested NAND entry."""
import argparse
from pathlib import Path
from derive_v249_private_callback_native_link_runner import derive as previous

DONE="echo 'V249_SC_AUTH_CALLBACK_LINK verified=1'"
NAND=r'^V250_NAND_BCTRL auth=[01] frame16=[01] link=[01] ctr=[01] abi=[01] userdata=[01] progressed=[01] reply=[01]$'
PASS=r'^V250_NAND_BCTRL auth=1 frame16=1 link=1 ctr=1 abi=1 userdata=1 progressed=1 reply=1$'
TRIAL=r'^V250_TRIAL_PASS trial=([1-9]|1[0-6])$'
STAGE=r'''# Explicit second binary from privately restored original Wii callbacks.
# Do not alter or rerun the already-verified V244 baseline native executable.
if python3 "$V110_SOURCE_ROOT/derive_v250_restored_callback_nand_harness.py" \
     "$work/harness.cpp" "$work/v250-harness.cpp" > "$work/v250-derive.log" 2>&1; then
  echo 'V250_STAGE derive=1'
else
  echo 'V250_STAGE derive=0'
  exit 1
fi
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
       -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include" \
       -c "$work/v250-harness.cpp" -o "$work/v250-harness.o" \
       > "$work/v250-compile.log" 2>&1; then
  echo 'V250_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py" "$work/v250-compile.log" harness || true
  echo 'V250_STAGE compile=0'
  exit 1
fi
if g++ "$work/v250-harness.o" "$work/v249-generated.o" "$work/loader.o" \
       -o "$work/v250-native" > "$work/v250-link.log" 2>&1; then
  echo 'V250_STAGE link=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v71_link_failure.py" "$work/v250-link.log" || true
  echo 'V250_STAGE link=0'
  exit 1
fi
if timeout 90 "$work/v250-native" "$work/private-v248.dol" owner-callback "$owner" \
      > "$work/v250-native.log" 2>&1; then
  echo 'V250_STAGE execute=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v178_native_failure.py" "$work/v250-native.log" "$work/v250-harness.cpp" || true
  python3 "$V110_SOURCE_ROOT/diagnose_v250_native_phase.py" "$work/v250-native.log" "$work/v250-harness.cpp" || true
  grep -E '^V250_CB_BEGIN candidate=1 reply=[01] captured=1$|^V250_NAND_BCTRL auth=[01] frame16=[01] link=[01] ctr=[01] abi=[01] userdata=[01] progressed=[01] reply=[01]$' "$work/v250-native.log" | sort -u || true
  echo 'V250_STAGE execute=0'
  exit 1
fi
test "$(grep -Ec '^V250_NAND_BCTRL auth=1 frame16=1 link=1 ctr=1 abi=1 userdata=1 progressed=1 reply=1$' "$work/v250-native.log")" -eq 16
test "$(grep -Ec '^V250_TRIAL_PASS trial=([1-9]|1[0-6])$' "$work/v250-native.log")" -eq 16
grep -E '^V250_NAND_BCTRL auth=[01] frame16=[01] link=[01] ctr=[01] abi=[01] userdata=[01] progressed=[01] reply=[01]$' "$work/v250-native.log" | sort -u
echo 'V250_SC_NAND_BCTRL verified=1'
'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(DONE)!=1:
        raise ValueError("V250 independently linked original callback candidate missing")
    return s.replace(DONE,DONE+"\n"+STAGE,1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
