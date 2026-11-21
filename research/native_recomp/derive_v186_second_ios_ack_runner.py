#!/usr/bin/env python3
"""V186 owner-original second IOS_Open native Starlet ACK, 16-trial gate."""
import argparse
from pathlib import Path
from derive_v185_sc_reply_next_runner import derive as previous

OLD='python3 "$here/derive_v185_sc_reply_next_harness.py"'
NEW='python3 "$here/derive_v186_second_ios_ack_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V185_SC_NEXT verified=1'"
PRE=r'^V186_IOS_PRE route=[01] prior=[01] intake=[01] clear=[01] open=[01] idle=[01] sc=[01]$'
ACK=r'^V186_SECOND_ACK ack=[01] y2=[01] irq=[01] queued=[01] consumed=[01] original=[01] cpu=[01] sc=[01]$'
STATE=r'^V186_ACK_STATE guest=[01] mail=[01] service=[01]$'
PASS_PRE=r'^V186_IOS_PRE route=1 prior=1 intake=1 clear=1 open=1 idle=1 sc=1$'
PASS_ACK=r'^V186_SECOND_ACK ack=1 y2=1 irq=1 queued=1 consumed=1 original=1 cpu=1 sc=1$'
PASS_STATE=r'^V186_ACK_STATE guest=1 mail=1 service=1$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V186 inherited private original runner source anchors differ")
    s=s.replace(OLD,NEW,1)
    # Bounded phase markers only: no compiler text or private paths.
    for phase,anchor in (("compile",'for unit in harness generated loader; do'),
                         ("link",'g++ "$work/harness.o" "$work/generated.o" "$work/loader.o"'),
                         ("execute",'"$work/native" "$work/private.dol" owner "$owner"')):
        if s.count(anchor)!=1:
            raise ValueError(f"V186 owner original-free {phase} build anchor count differs")
        marker=('echo "V186_BUILD unit=$unit"'
                if phase=="compile" else f"echo 'V186_BUILD {phase}=1'")
        if phase=="compile":
            # Shell for-loop body executes once for each public build unit.
            s=s.replace(anchor,anchor+'\n  '+marker,1)
        else:
            s=s.replace(anchor,marker+'\n'+anchor,1)
    s=s.replace(FAIL,
        '  grep -E "^(V186_BUILD unit=(harness|generated|loader)|V186_BUILD (link|execute)=1|V77_COMPILE_UNIT (harness|generated|loader|generator)|V67_NATIVE_ASSERTION id=[0-9]{3,4})$" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(FAIL,
        '  grep -E "'+PRE+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+ACK+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS_PRE}' "$log" | sort -u
test "$(grep -Ec '{PASS_PRE}' "$log")" -eq 16
grep -E '{PASS_ACK}' "$log" | sort -u
test "$(grep -Ec '{PASS_ACK}' "$log")" -eq 16
grep -E '{PASS_STATE}' "$log" | sort -u
test "$(grep -Ec '{PASS_STATE}' "$log")" -eq 16
echo 'V186_SECOND_ACK verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
