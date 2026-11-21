#!/usr/bin/env python3
"""V208 original second IOS_Open guest-yield reply publication runner."""
import argparse
from pathlib import Path
from derive_v207_sc_y2_helper_next_runner import derive as previous

OLD='python3 "$here/derive_v207_sc_y2_helper_next_harness.py"'
NEW='python3 "$here/derive_v208_sc_y2_reply_publication_harness.py"'
DONE="echo 'V207_SC_Y2_HELPER_NEXT verified=1'"
PATTERN=r'^V208_Y2_REPLY step=[01] wire=[01] opened=[01] signal=[01] drained=[01] cpu=[01] sc=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V208_Y2_REPLY step=1 wire=1 opened=1 signal=1 drained=1 cpu=1 sc=1 pc=80529434 lr=80526cb0$'
KIND=r'^V208_Y2_KIND immediate=[01] event=[01] fs=[01] file=[01] es=[01] negative=[01] result=-?[0-9]{1,4}$'
ARGS=r'^V208_Y2_OPEN_ARGS zero=[01] mapped=[01] mode_valid=[01] mode_hi8=[01] invalid=[01]$'
MODE=r'^V208_Y2_MODE swap_valid=[01] mem1virt=[01] mem2virt=[01] mem1phys=[01] mem2phys=[01] same_path=[01] aligned=[01] path_slash=[01]$'
SEND_PATTERN=r'^V208_Y2_SEND witness=[01] ptr=[01] slash=[01] mode_valid=[01] mode_mem2=[01]$'
STABLE_PATTERN=r'^V208_Y2_STABLE sent=[01] path=[01] mode=[01]$'
SWAP_PATTERN=r'^V208_Y2_SWAP path_mode=[01] mode_mem2=[01] mode_mapped=[01] mode_slash=[01] mode_string=[01]$'
LAYOUT_PATTERN=r'^V208_Y2_LAYOUT ptr0c=[01] ptr10=[01] ptr14=[01] ptr18=[01] ptr1c=[01] mode0c=[01] mode10=[01] mode14=[01] mode18=[01] mode1c=[01]$'
BASE_PATTERN=r'^V208_Y2_BASE old_valid=[01] old_reply=[01] old_path=[01] old_mode=[01] old_open=[01] same_ptr=[01]$'
ORIGIN_PATTERN=r'^V208_Y2_ORIGIN pc_text=[01] lr_text=[01] mem1=[01] mem2=[01] reused=[01] overlap=[01] a_block=[01] a_open=[01] a_reply=[01] req_regs=[0-9]{1,3} path_regs=[0-9]{1,3} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$'
PATHCLASS_PATTERN=r'^V208_Y2_PATHCLASS valid=[01] dev=[01] stm=[01] fs=[01] es=[01] shared2=[01] sysconf=[01] title=[01]$'
ALIAS_PATTERN=r'^V208_Y2_ALIAS cached=[01] uncached=[01] same_ptr=[01] same_header=[01] path_cached=[01] path_uncached=[01] path_coherent=[01]$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V208 inherited original V207 owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V208 original-native runner failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+KIND+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+ARGS+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+MODE+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+SEND_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+STABLE_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+SWAP_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+LAYOUT_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+BASE_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+ORIGIN_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+PATHCLASS_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  grep -E "'+ALIAS_PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V208_SC_Y2_REPLY_PUBLICATION verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
