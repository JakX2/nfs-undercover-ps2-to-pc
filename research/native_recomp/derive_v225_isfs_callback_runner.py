#!/usr/bin/env python3
"""V225 native callback AOT-root experiment with original V177 execution."""
import argparse
from pathlib import Path
from derive_v177_sc_reply_next_runner import derive as previous

OLD='python3 "$here/derive_v79_reply_generator.py" "$here/generate_start_to_ipc_ack_v77.cpp" "$work/generator.cpp"'
NEW='python3 "$here/derive_v225_isfs_callback_generator.py" "$here/generate_start_to_ipc_ack_v77.cpp" "$work/generator.cpp"'
AFTER="echo 'V79_STAGE generation_complete'"
DONE="echo 'V177_SC_REPLY_NEXT verified=1'"
PROBE=r'^V225_CB_ANALYZER rooted=1 analyzed=1$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(AFTER)!=1 or s.count(DONE)!=1:
        raise ValueError("V225 inherited V177 native runner/generator seam changed")
    s=s.replace(OLD,NEW,1)
    # The generator's private progress log stays in the owner's mktemp.
    # Require a public fixed-string proof without echoing private details.
    s=s.replace(AFTER,AFTER+"""
grep -Fx 'V225_CB_ANALYZER rooted=1 analyzed=1' "$work/generation.log" >/dev/null || {
  echo 'V225_CB_AOT_ROOT verified=0'
  exit 1
}
echo 'V225_CB_AOT_ROOT verified=1'""",1)
    return s.replace(DONE,DONE+"""
grep -Fx 'V225_CB_AOT_ROOT verified=1' "$log"
echo 'V225_SC_ISFS_CALLBACK_AOT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
