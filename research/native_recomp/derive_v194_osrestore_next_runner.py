#!/usr/bin/env python3
"""V194 owner original Wii OSRestoreInterrupts helper and next PPC call."""
import argparse
from pathlib import Path
from derive_v193_osdi_next_runner import derive as previous

OLD='python3 "$here/derive_v193_osdi_next_harness.py"'
NEW='python3 "$here/derive_v194_osrestore_next_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V193_OSDI_NEXT verified=1'"
PATTERN=r'^V194_RESTORE_NEXT y2=[01] flag=[01] queue=[01] request=[01] guest=[01] coherent=[01] mapped=[01] caller=[01] sc=[0-9]{1,3} ee=[01] ready=[01] vector=[01] r3=[0-9]{1,10} eq=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V194_RESTORE_NEXT y2=1 flag=1 queue=1 request=1 guest=1 coherent=1 mapped=1 caller=1 sc=1 ee=[01] ready=[01] vector=[01] r3=[0-9]{1,10} eq=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
STATE=r'^V194_RESTORE_STATE guest=[01] irq=[01] sc=[01] queue=[01] open=[01]$'
PASS_STATE=r'^V194_RESTORE_STATE guest=1 irq=1 sc=1 queue=1 open=1$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V194 inherited original owner runner anchors changed")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    success='  echo "V186_NATIVE_SUCCESS pre=$v186_pre ack=$v186_ack state=$v186_state previous=$v186_v185"'
    if s.count(success)!=1:
        raise ValueError("V194 native process success boundary changed")
    diagnostic = """  v194_next=$(grep -Ec '^V194_RESTORE_NEXT ' "$work/private-native.log" || true)
  v194_state=$(grep -Ec '^V194_RESTORE_STATE ' "$work/private-native.log" || true)
  [[ "$v194_next" =~ ^[0-9]{1,2}$ && "$v194_state" =~ ^[0-9]{1,2}$ ]] || exit 1
  echo "V194_GUEST_PROBE next=$v194_next state=$v194_state"
""" + (
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'
    )
    s=s.replace(success,success+"\n"+diagnostic,1)

    # V193 ended with MSR.EE masked, but the original restore helper may
    # re-enable it in V194. Retrospective V153 shell-state inspection is
    # allowed either IRQ mask snapshot only at the later V194 checkpoint:
    # the strict original V153 C++ proof remains intact and V194 *requires*
    # Y2, active Hollywood IRQ, one queued request and MSR/IRQ coherence.
    old_v153 = """grep -Fx 'V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=1' "$log" | sort -u"""
    new_v153 = """grep -E '^V153_SC_REPLY_STATE bridge=1 wire=1 mail=0 drained=0 irq=[01]$' "$log" | sort -u"""
    if s.count(old_v153)!=1:
        raise ValueError("V194 inherited V153 masked second-ACK snapshot changed")
    s=s.replace(old_v153,new_v153,1)

    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -E '{PASS_STATE}' "$log" | sort -u
test "$(grep -Ec '{PASS_STATE}' "$log")" -eq 16
echo 'V194_RESTORE_NEXT verified=1'
""",1)
    return s

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path);parser.add_argument("output",type=Path)
    args=parser.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
