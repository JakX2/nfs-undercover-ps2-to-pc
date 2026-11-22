#!/usr/bin/env python3
"""V260: sixteen original-game NAND-to-PPCMSG prewrite observation trials."""
import argparse
from pathlib import Path
from derive_v259_ipc_reentry_runner import derive as previous

OLD='python3 "$V110_SOURCE_ROOT/derive_v259_ipc_reentry_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v260_ipc_ppcmsg_boundary_harness.py"'
DONE="echo 'V259_SC_IPC_REENTRY verified=1'"
PATTERN=r'^V260_PPCMSG_BOUNDARY guest=[01] aligned=[01] mapped=[01] fresh=[01] coherent=[01] reply=[01] open=[01] mem2=[01] mode_ok=[01] path_phys=[01] path_alias=[01] idle=[01] prewrite=1$'
PASS=r'^V260_PPCMSG_BOUNDARY guest=1 aligned=1 mapped=1 fresh=1 coherent=1 reply=[01] open=[01] mem2=[01] mode_ok=[01] path_phys=[01] path_alias=[01] idle=[01] prewrite=1$'
TRIAL=r'^V260_NAND_GUEST callback=1 event=1 memory=1 trial=([1-9]|1[0-6])$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V260 inherited owner-original V259 runner changed")
    s=s.replace(OLD,NEW,1)
    old="V259_NAND_GUEST callback=1 reentry=1 memory=1"
    new="V260_NAND_GUEST callback=1 event=1 memory=1"
    if s.count(old)!=9:
        raise ValueError("V260 inherited V259 final state trial gate changed")
    s=s.replace(old,new)
    old_diag="V259_NAND_GUEST callback=[01] reentry=[01] memory=[01]"
    new_diag="V260_NAND_GUEST callback=[01] event=[01] memory=[01]"
    if s.count(old_diag)!=1:
        raise ValueError("V260 inherited V259 failure diagnostic changed")
    s=s.replace(old_diag,new_diag)
    fail="  echo 'V250_STAGE execute=0'"
    diag='  grep -E "^V260_CALL_FRONTIER guest=[01] coherent=[01] mapped=[01] calls=[0-9]{1,3} sc=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$|'+PATTERN+'|^V260_NAND_GUEST callback=[01] event=[01] memory=[01] trial=([1-9]|1[0-6])$" "$work/v250-native.log" | sort -u || true'
    if s.count(fail)!=1:
        raise ValueError("V260 inherited native failure hook changed")
    s=s.replace(fail,diag+'\n'+fail,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$work/v250-native.log" | sort -u || true
grep -E '^V260_CALL_FRONTIER guest=1 coherent=1 mapped=1 calls=64 sc=[0-9]{{1,3}} pc=[0-9a-f]{{8}} lr=[0-9a-f]{{8}}$' "$work/v250-native.log" | sort -u || true
msg="$(grep -Ec '{PASS}' "$work/v250-native.log" || true)"
calls="$(grep -Ec '^V260_CALL_FRONTIER guest=1 coherent=1 mapped=1 calls=64 sc=[0-9]{{1,3}} pc=[0-9a-f]{{8}} lr=[0-9a-f]{{8}}$' "$work/v250-native.log" || true)"
test "$((msg+calls))" -eq 16
test "$msg" -eq 0 -o "$calls" -eq 0
test "$(grep -Ec '{TRIAL}' "$work/v250-native.log")" -eq 16
for n in $(seq 1 16); do
  grep -Fx "V260_NAND_GUEST callback=1 event=1 memory=1 trial=$n" "$work/v250-native.log"
done
if (( msg != 0 ));then echo 'V260_POSTIPC_RESULT kind=ppcmsg trials=16'
else echo 'V260_POSTIPC_RESULT kind=calls trials=16';fi
echo 'V260_SC_POSTIPC_EVENT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
