#!/usr/bin/env python3
"""V229 original negative reply cache successor with verified ISFS AOT root."""
import argparse
import re
import sys
sys.setrecursionlimit(6000)
from pathlib import Path
from derive_v228_sc_y1_negative_flag_runner import derive as previous
OLD='python3 "$here/derive_v228_sc_y1_negative_flag_harness.py"'
NEW='python3 "$here/derive_v229_sc_y1_post_cache_harness.py"'
DONE="echo 'V228_SC_Y1_NEGATIVE_FLAG verified=1'"
AFTER="for unit in harness generated loader; do"
PATTERN=r'^V229_NEG_POST_CACHE clear=[01] negative=[01] guest=[01] caller=[01] sc=[01] context=[01] callback=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V229_NEG_POST_CACHE clear=1 negative=1 guest=1 caller=1 sc=1 context=[01] callback=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1 or s.count(AFTER)!=1:
        raise ValueError("V229 inherited original V228 owner runner changed")
    s=s.replace(OLD,NEW,1)
    generator=re.compile(
      r'python3 "\$here/(derive_v[0-9a-z_]+_generator\.py)" '
      r'"\$here/generate_start_to_ipc_ack_v77\.cpp" '
      r'"\$work/generator\.cpp"')
    matches=list(generator.finditer(s))
    if len(matches)!=1:
        raise ValueError("V229 expected exactly one inherited active AOT generator")
    s=s[:matches[0].start()]+
      'python3 "$here/derive_v225_isfs_callback_generator.py" "$here/generate_start_to_ipc_ack_v77.cpp" "$work/generator.cpp"'+
      s[matches[0].end():]
    s=s.replace(AFTER,"""grep -Fx 'V225_CB_ANALYZER rooted=1 analyzed=1' "$work/generation.log" >/dev/null || {
  echo 'V229_CALLBACK_ROOT verified=0'
  exit 1
}
echo 'V229_CALLBACK_ROOT verified=1'
"""+AFTER,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V229 native owner failure marker changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V229_SC_Y1_POST_CACHE verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
