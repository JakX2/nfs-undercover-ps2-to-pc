#!/usr/bin/env python3
"""V125 owner-original next-call runner after SC helper."""
from derive_v124_sc_second_save_runner import derive as previous
from pathlib import Path
import argparse
EDITS=[
 ("derive_v124_sc_second_save_harness.py","derive_v125_sc_helper_harness.py"),
 ("V124_TRIAL_PASS","V125_TRIAL_PASS"),
 ("V124 recovered continuous original __start->SC IOS second register-save call and successor",
  "V125 recovered continuous original __start->SC IOS SC helper continuation"),
 ("V124_STAGE native_test_passed","V125_STAGE native_test_passed"),
 ("V124_NATIVE_EXIT","V125_NATIVE_EXIT"),
 ("stage=124","stage=125")
]
def derive(source):
    s=previous(source)
    for a,b in EDITS:
        if a not in s:raise ValueError("V125 runner missing source anchor: "+a)
        s=s.replace(a,b)
    build='python3 "$here/make_start_to_ipc_ack_v77.py"'
    geometry='python3 "$here/test_v77_continuous_ipc_ack_geometry.py"'
    if s.count(build)!=1 or s.count(geometry)!=1:
        raise ValueError("V125 fixture hooks missing or duplicated")
    s=s.replace(build,'python3 "$here/make_start_to_sc_helper_v125.py"',1)
    s=s.replace(geometry,'python3 "$here/test_v125_sc_helper_geometry.py"',1)
    fail="  echo 'V125_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V125 fail marker missing")
    s=s.replace(fail,"  grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    private='  python3 "$here/classify_v125_runtime_shape.py" "$work/private-native.log" || true\n'
    s=s.replace(fail,private+fail,1)
    stage="echo 'V104_STAGE generation_complete'"
    if s.count(stage)!=1:raise ValueError("V125 generated target reporting anchor missing")
    target='''if grep -Eiq "func_8051[eE]5[bB][cC]" "$work/generated/output.cpp"; then
  echo 'V125_GENERATED_TARGET present=1'
else
  echo 'V125_GENERATED_TARGET present=0'
fi'''
    s=s.replace(stage,stage+"\n"+target,1)
    marker="  echo 'V125_NATIVE_EXIT ok=0'"
    if s.count(marker)!=1:raise ValueError("V125 exception output anchor")
    s=s.replace(marker,"  grep -E '^V125_EXCEPTION_SITE pc=[0-9a-f]{8} lr=[0-9a-f]{8} phase=[01] kind=[01]$' \"$work/private-native.log\" | sort -u || true\n"+marker,1)
    catalog='  python3 "$here/classify_v67_native_failure.py" "$work/private-native.log" "$work/harness.cpp" || true\n'
    s=s.replace(fail,catalog+fail,1)
    status_line='  grep -E "^V125_EXCEPTION_STEPS delta=[0-9]{1,6}$" "$work/private-native.log" | sort -u || true\n'
    s=s.replace(fail,status_line+fail,1)
    trace='  grep -E "^V125_TRACE_CALL seq=[0-9]{1,2} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$|^V125_OPCODE_CLASS first_branch=[01] first_mem=[01] second_branch=[01] second_mem=[01]$" "$work/private-native.log" | sort -u || true\n'
    s=s.replace(fail,trace+fail,1)
    detail='  grep -E "^V125_OPCODE_DETAIL major0=[0-9]{1,2} major1=[0-9]{1,2} xo0=[0-9]{1,4} zero0=[01] zero1=[01]$" "$work/private-native.log" | sort -u || true\n'
    s=s.replace(fail,detail+fail,1)
    fixture_stage="echo 'V104_STAGE fixture_generated'"
    if s.count(fixture_stage)!=1:raise ValueError("V125 fixture stage unavailable")
    coverage='python3 "$here/diagnose_v125_fixture_coverage.py" "$work/private.dol" "$owner"'
    s=s.replace(fixture_stage,fixture_stage+"\n"+coverage,1)
    fail_marker="echo 'V71 STM geometry guard failed' >&2"
    if s.count(fail_marker)!=1:raise ValueError("V125 missing private geometry failure gate")
    s=s.replace(fail_marker,
                'grep -E "^V125_GEOMETRY_FAILURE code=[0-9]{1,2} valueerror=[01]$" "$work/private-geometry.log" || true\n'+fail_marker,1)
    gate="echo 'V71 STM geometry guard failed' >&2"
    if s.count(gate)!=1:raise ValueError("V125 geometry branch not unique")
    classify='''
if grep -Eiq 'ModuleNotFoundError|ImportError' "$work/private-geometry.log"; then echo 'V125_GEOMETRY_KIND import=1 type=0 value=0 other=0'
elif grep -Eiq 'TypeError|AttributeError' "$work/private-geometry.log"; then echo 'V125_GEOMETRY_KIND import=0 type=1 value=0 other=0'
elif grep -Eiq 'ValueError' "$work/private-geometry.log"; then echo 'V125_GEOMETRY_KIND import=0 type=0 value=1 other=0'
else echo 'V125_GEOMETRY_KIND import=0 type=0 value=0 other=1'; fi
grep -E '^V125_GEOMETRY_FAILURE code=[0-9]{1,2} valueerror=[01]$' "$work/private-geometry.log" || true
'''
    s=s.replace(gate,classify+gate,1)
    coverage='python3 "$here/diagnose_v125_fixture_coverage.py" "$work/private.dol" "$owner"'
    if s.count(coverage)!=1:raise ValueError("V125 coverage marker missing")
    s=s.replace(coverage,coverage+"\necho 'V125_STAGE_CHECK after_probe=1'",1)
    geometry='python3 "$here/test_v125_sc_helper_geometry.py"'
    if s.count(geometry)!=1:raise ValueError("V125 geometry marker missing")
    s=s.replace(geometry,"echo 'V125_STAGE_CHECK before_geometry=1'\n"+geometry,1)
    stages=("echo 'V104_STAGE geometry_verified'","echo 'V79_STAGE geometry_verified'")
    selected=[mark for mark in stages if s.count(mark)==1]
    if len(selected)!=1:raise ValueError("V125 geometry stage marker ambiguous")
    s=s.replace(selected[0],"echo 'V125_STAGE_CHECK after_geometry=1'\n"+selected[0],1)
    command='python3 "$here/test_v125_sc_helper_geometry.py" "$work/private.dol" "$owner"   > "$work/private-geometry.log" 2>&1 || {'
    if s.count(command)!=1:
        raise ValueError("V125 geometry command guard missing")
    s=s.replace(command,command+"\n    echo 'V125_STAGE_CHECK geometry_failure_branch=1'",1)
    # Replace the entire inherited geometry shell block. Inserting a newline
    # into the command head alone can change the errexit/OR-list semantics.
    begin="echo 'V125_STAGE_CHECK before_geometry=1'\n"+command
    after="echo 'V125_STAGE_CHECK after_geometry=1'"
    if s.count(begin)!=1 or s.count(after)!=1:
        raise ValueError("V125 conditional geometry block not unique")
    a=s.index(begin)
    b=s.index(after,a)
    old_block=s[a:b]
    if old_block.count("V125_GEOMETRY_KIND import=1")!=1 or \
       old_block.count("V125_STAGE_CHECK geometry_failure_branch=1")!=1:
        raise ValueError("V125 inherited geometry safety guard missing")
    safe_block="""echo 'V125_STAGE_CHECK before_geometry=1'
if python3 "$here/test_v125_sc_helper_geometry.py" "$work/private.dol" "$owner" \
  > "$work/private-geometry.log" 2>&1; then
  echo 'V125_GEOMETRY_STATUS ok=1'
else
  echo 'V125_STAGE_CHECK geometry_failure_branch=1'
"""+classify+"""  echo 'V125_GEOMETRY_STATUS ok=0'
  echo 'V71 STM geometry guard failed' >&2
  exit 1
fi
"""
    s=s[:a]+safe_block+s[b:]
    # Surface only bounded diagnostic fields from the private generator log.
    classifier='python3 "$here/classify_v67_generator_failure.py" "$work/generation.log" "$work/generator.cpp"'
    if s.count(classifier)!=1:
        raise ValueError("V125 generator failure classifier anchor missing or duplicated")
    diagnostic='grep -E \'^V125_BAD_BRANCH site=[0-9a-f]{8} major=[0-9]{1,2} link=[01] absolute=[01]$\' "$work/generation.log" | head -n 1 || true'
    s=s.replace(classifier,diagnostic+"\\n    "+classifier,1)
    generated='python3 "$here/derive_v104_sc_async_submit_generator.py"'
    if s.count(generated)!=1:
        raise ValueError("V125 generator runner reference missing or duplicated")
    s=s.replace(generated,'python3 "$here/derive_v125_sc_helper_generator.py"',1)
    good="echo 'V125_STAGE native_test_passed'"
    if s.count(good)!=1:raise ValueError("V125 pass marker missing")
    s=s.replace(good,good+"""
grep -Fx 'V124_NEXT_CALL pc=8051e5bc lr=8051e054 route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V125_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    old="candidate=\"$(grep -E '^V124_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(old)!=1:raise ValueError("V125 dynamic candidate anchor")
    s=s.replace(old,"candidate=\"$(grep -E '^V125_NEXT_CALL pc=[0-9a-f]{8}",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
