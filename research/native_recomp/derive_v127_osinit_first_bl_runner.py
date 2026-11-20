#!/usr/bin/env python3
"""V127 private original OSInit first BL next-call native execution."""
from pathlib import Path
import argparse
from derive_v125_sc_helper_runner import derive as previous
from derive_v126_sc_post_gpr_runner import EDITS as post_gpr_edits

def derive(source):
    s=previous(source)
    for a,b in post_gpr_edits:
        if a not in s:raise ValueError("V127 runner source anchor missing: "+a)
        s=s.replace(a,b)
    s=s.replace("V126","V127")
    s=s.replace("stage=126","stage=127")
    s=s.replace("V127 recovered continuous original __start->SC IOS post-helper GPR-save and next call",
                "V127 recovered original OSInit first authenticated BL after post-SC GPR save")
    fail="  echo 'V127_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V127 fail marker missing")
    s=s.replace(fail,"  grep -E '^V127_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    # Diagnose a successful native process that misses a strict checkpoint.
    # Only emit bounded marker counts and an observed callsite, never translated code.
    diagnostics='''echo "V127_NATIVE_COUNTS start=$(grep -Ec '^V110_TRIAL_START trial=[0-9]{1,2}$' "$log" || true) pass=$(grep -Ec '^V127_TRIAL_PASS trial=[0-9]{1,2}$' "$log" || true) next=$(grep -Ec '^V127_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" || true) prior=$(grep -Fc 'V125_NEXT_CALL pc=80545150 lr=8051e05c route=1 wire=1 abi=1 text=1' "$log" || true)"
grep -E '^V127_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' "$log" | sort -u || true
'''
    log_anchor='log="$work/private-native.log"'
    if s.count(log_anchor)!=1:raise ValueError("V127 native log marker missing")
    s=s.replace(log_anchor,log_anchor+"\n"+diagnostics,1)
    marker="echo 'V127_STAGE native_test_passed'"
    if s.count(marker)!=1:raise ValueError("V127 success marker missing")
    s=s.replace(marker,marker+"""
grep -Fx 'V125_NEXT_CALL pc=80545150 lr=8051e05c route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V127_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V127_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    prior="candidate=\"$(grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(prior)!=1:raise ValueError("V127 next call marker differs")
    s=s.replace(prior,"candidate=\"$(grep -E '^V127_NEXT_CALL pc=[0-9a-f]{8}",1)
    generator='python3 "$here/derive_v125_sc_helper_generator.py"'
    if s.count(generator)!=1:raise ValueError("V127 generator reference missing")
    s=s.replace(generator,'python3 "$here/derive_v127_osinit_first_bl_generator.py"',1)
    after="echo 'V125_CANONICAL result=verified'"
    if s.count(after)!=1:raise ValueError("V127 authenticated fixture checkpoint missing")
    late='''python3 "$here/restore_v127_osinit_tail.py" "$work/private.dol" "$owner" "$work/osinit-v127.dol" \
  > "$work/v127-restore-private.log" 2>&1 || {
  echo 'V127_OSINIT_RESTORE ok=0'
  exit 1
}
mv -- "$work/osinit-v127.dol" "$work/private.dol"
echo 'V127_OSINIT_RESTORE ok=1'
'''
    s=s.replace(after,after+"\n"+late,1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
