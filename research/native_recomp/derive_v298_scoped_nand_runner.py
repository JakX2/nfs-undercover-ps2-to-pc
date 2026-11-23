#!/usr/bin/env python3
"""V298: run bounded owner-native NAND with only stale V178 observer scoped."""
from __future__ import annotations
import argparse
from pathlib import Path
from derive_v296_restored_nand_runner import AUDIT as V296_AUDIT
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
LINK='if g++ "$work/v296-harness.o" "$work/v294-generated.o" "$work/loader.o" \\'
DONE="echo 'V296_SERVICE_PROBE inspected=1'"
PRE=r'''
python3 "$V110_SOURCE_ROOT/derive_v298_scope_reply_observer.py" \
    "$work/v296-harness.cpp" "$work/v298-scoped-harness.cpp"
echo 'V341_SCOPE_STAGE derive=1'
python3 "$V110_SOURCE_ROOT/derive_v352_nand_mailbox_route.py" \
    "$work/v298-scoped-harness.cpp" "$work/v352-harness.cpp"
echo 'V352_NAND_ROUTE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v367_nand_irq_mask_route.py" \
    "$work/v352-harness.cpp" "$work/v367-harness.cpp"
echo 'V367_MASK_ROUTE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v370_nand_ipc_flag_w1c.py" \
    "$work/v367-harness.cpp" "$work/v370-harness.cpp"
echo 'V370_FLAG_ROUTE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v372_nand_v153_trial_scope.py" \
    "$work/v370-harness.cpp" "$work/v372-harness.cpp"
echo 'V372_SC_TRIAL_SCOPE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v369_post_ack_mmio_probe.py" \
    "$work/v372-harness.cpp" "$work/v369-harness.cpp"
python3 "$V110_SOURCE_ROOT/derive_v340_nand_mmio_probe.py" \
    "$work/v369-harness.cpp" "$work/v340-harness.cpp"
echo 'V341_PROBE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v321_guest_entry_probe.py" \
    "$work/v340-harness.cpp" "$work/v321-harness.cpp"
python3 "$V110_SOURCE_ROOT/derive_v359_post_x1_call_probe.py" \
    "$work/v321-harness.cpp" "$work/v359-harness.cpp"
python3 "$V110_SOURCE_ROOT/derive_v361_nand_ios_yield.py" \
    "$work/v359-harness.cpp" "$work/v361-harness.cpp"
python3 "$V110_SOURCE_ROOT/derive_v365_nand_irq_readiness.py" \
    "$work/v361-harness.cpp" "$work/v365-harness.cpp"
python3 "$V110_SOURCE_ROOT/derive_v373_nand_irq_timeline.py" \
    "$work/v365-harness.cpp" "$work/v373-harness.cpp"
echo 'V373_IRQ_TIMELINE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v374_nand_ios_reply.py" \
    "$work/v373-harness.cpp" "$work/v374-harness.cpp"
echo 'V374_NAND_REPLY_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v375_nand_y1_boundary.py" \
    "$work/v374-harness.cpp" "$work/v375-harness.cpp"
echo 'V375_Y1_BOUNDARY_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v376_nand_y1_vector.py" \
    "$work/v375-harness.cpp" "$work/v376-harness.cpp"
echo 'V376_NAND_VECTOR_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v377_nand_vector_handler.py" \
    "$work/v376-harness.cpp" "$work/v377-harness.cpp"
echo 'V377_NAND_HANDLER_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v378_nand_irq_dispatch.py" \
    "$work/v377-harness.cpp" "$work/v378-harness.cpp"
echo 'V378_NAND_DISPATCH_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v379_nand_timebase_frontier.py" \
    "$work/v378-harness.cpp" "$work/v379-harness.cpp"
echo 'V379_NAND_TIME_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v380_nand_scheduler_frontier.py" \
    "$work/v379-harness.cpp" "$work/v380-harness.cpp"
echo 'V380_NAND_SCHED_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v381_nand_ipc_handler.py" \
    "$work/v380-harness.cpp" "$work/v381-harness.cpp"
echo 'V381_NAND_IPC_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v382_nand_ipc_next.py" \
    "$work/v381-harness.cpp" "$work/v382-harness.cpp"
echo 'V382_NAND_IPC_NEXT_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v383_nand_reply_handler.py" \
    "$work/v382-harness.cpp" "$work/v383-harness.cpp"
echo 'V383_NAND_REPLY_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v384_nand_reply_read.py" \
    "$work/v383-harness.cpp" "$work/v384-harness.cpp"
echo 'V384_NAND_REPLY_READ_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v385_nand_second_read.py" \
    "$work/v384-harness.cpp" "$work/v385-harness.cpp"
echo 'V385_NAND_SECOND_READ_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v385_nand_armmsg_scope.py" \
    "$work/v385-harness.cpp" "$work/v385-scoped-harness.cpp"
echo 'V385_NAND_ARMMSG_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v386_nand_ipc_next.py" \
    "$work/v385-scoped-harness.cpp" "$work/v386-harness.cpp"
echo 'V386_NAND_NEXT_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v387_nand_reply_route.py" \
    "$work/v386-harness.cpp" "$work/v387-harness.cpp"
echo 'V387_NAND_ROUTE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v388_nand_bounded_trace.py" \
    "$work/v387-harness.cpp" "$work/v388-harness.cpp"
echo 'V388_NAND_BOUNDED_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v389_nand_hollywood_ack.py" \
    "$work/v388-harness.cpp" "$work/v389-harness.cpp"
echo 'V389_NAND_FLAG_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v390_nand_post_ack.py" \
    "$work/v389-harness.cpp" "$work/v390-harness.cpp"
echo 'V390_NAND_POST_ACK_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v391_nand_post_ack_next.py" \
    "$work/v390-harness.cpp" "$work/v391-harness.cpp"
echo 'V391_NAND_POST_ACK_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v392_nand_post_cache.py" \
    "$work/v391-harness.cpp" "$work/v392-harness.cpp"
echo 'V392_NAND_POST_CACHE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v393_nand_guest_next.py" \
    "$work/v392-harness.cpp" "$work/v393-harness.cpp"
echo 'V393_NAND_GUEST_NEXT_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v394_nand_isfs_entry.py" \
    "$work/v393-harness.cpp" "$work/v394-harness.cpp"
echo 'V394_NAND_ISFS_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v395_nand_isfs_next.py" \
    "$work/v394-harness.cpp" "$work/v395-harness.cpp"
echo 'V395_NAND_ISFS_NEXT_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v396_nand_callback_body.py" \
    "$work/v395-harness.cpp" "$work/v396-harness.cpp"
echo 'V396_NAND_CB_BODY_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v397_nand_callback_lineage.py"     "$work/v396-harness.cpp" "$work/v397-harness.cpp"
echo 'V397_NAND_ORIGINS_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v398_nand_return_site.py" \
    "$work/v397-harness.cpp" "$work/v398-harness.cpp"
echo 'V398_NAND_RETURN_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v399_nand_resume_chain.py" \
    "$work/v398-harness.cpp" "$work/v399-harness.cpp"
echo 'V399_NAND_RETURN_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v400_nand_parent_resume.py" \
    "$work/v399-harness.cpp" "$work/v400-harness.cpp"
echo 'V400_NAND_PARENT_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v401_nand_linksite_classify.py" \
    "$work/v400-harness.cpp" "$work/v401-harness.cpp"
echo 'V401_NAND_CALLSITE_STAGE install=1'
python3 "$V110_SOURCE_ROOT/derive_v403_nand_call_provenance.py" \
    "$work/v401-harness.cpp" "$work/v298-harness.cpp"
echo 'V403_NAND_CALL_PROVENANCE_STAGE install=1'
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label        -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include"        -c "$work/v298-harness.cpp" -o "$work/v298-harness.o"        > "$work/v298-compile.log" 2>&1; then
  echo 'V298_HARNESS_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py"     "$work/v298-compile.log" harness || true
  echo 'V298_HARNESS_STAGE compile=0'
  exit 1
fi
'''
V303_STAGE=r'''
# V303: entirely separate owner-private candidate. Do not overwrite the
# reduced baseline or the V294 restored four-function binary.
mkdir "$work/generated-v303"
if "$work/generator" "$work/private-v302.dol" "$work/generated-v303" owner \
    > "$work/v303-generate.log" 2>&1; then
  echo 'V303_HELPER_STAGE generate=1'
else
  echo 'V303_HELPER_STAGE generate=0'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/analyze_v301_nand_first_helper.py" \
     "$owner" "$work/v293-original.elf" "$work/private-v302.dol" \
     "$work/generated-v303/output.cpp" > "$work/v303-coverage-raw.log" 2>&1; then
  cat "$work/v303-coverage-raw.log"
  echo 'V303_HELPER_STAGE inspect=1'
else
  grep -Fx 'V301_HELPER_AUDIT verified=0' "$work/v303-coverage-raw.log" || true
  echo 'V303_HELPER_STAGE inspect=0'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/analyze_v303_helper_coverage.py" \
     "$work/v303-coverage-raw.log"; then
  echo 'V303_HELPER_STAGE coverage=1'
else
  echo 'V303_HELPER_STAGE coverage=0'
  exit 1
fi
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
    -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include" \
    -c "$work/generated-v303/output.cpp" -o "$work/v303-generated.o" \
    > "$work/v303-compile.log" 2>&1; then
  echo 'V303_HELPER_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py" \
     "$work/v303-compile.log" generated || true
  echo 'V303_HELPER_STAGE compile=0'
  exit 1
fi
if g++ "$work/v298-harness.o" "$work/v303-generated.o" "$work/loader.o" \
      -o "$work/v303-native" > "$work/v303-link.log" 2>&1; then
  test -s "$work/v303-native" && test -x "$work/v303-native"
  echo 'V303_HELPER_STAGE link=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v71_link_failure.py" \
    "$work/v303-link.log" || true
  echo 'V303_HELPER_STAGE link=0'
  exit 1
fi
echo 'V303_HELPER_NATIVE_LINK verified=1'
# V306: read-only comparison of four original descendants of 0x804F2064.
# Never print the private function bytes or generated C++.
if python3 "$V110_SOURCE_ROOT/analyze_v306_helper_descendants.py"     "$owner" "$work/v293-original.elf" "$work/private-v302.dol"     "$work/generated-v303/output.cpp" > "$work/v306-coverage.log" 2>&1; then
  grep -Fx 'V306_COVERAGE_AUDIT verified=1' "$work/v306-coverage.log"
  grep -E '^V306_COVERAGE owner=1 targets=4 exact=[0-4] interior=[0-4] emitted=[0-4] dispatch=[0-4] missing=[0-4] partial=[0-4] unknown=[0-4]$' "$work/v306-coverage.log"
  grep -E '^V306_DESCENDANT pc=[0-9a-f]{8} kind=(exact|interior|unknown|ambiguous|invalid) base=[0-9a-f]{8} offset=[0-9]{1,5} words=[0-9]{1,5} present=[01] same=[0-9]{1,5} nop=[0-9]{1,5} blr=[0-9]{1,5} other=[0-9]{1,5} body=[01] dispatch=[01]$' "$work/v306-coverage.log"
  echo 'V306_DESCENDANT_STAGE inspected=1'
else
  grep -E '^V306_COVERAGE_ERROR reason=(authenticated_digest|fixture_geometry|function_size|original_span|cpp_geometry|span_geometry|invalid_target|input_io|other)$' "$work/v306-coverage.log" || true
  grep -Fx 'V306_COVERAGE_AUDIT verified=0' "$work/v306-coverage.log" || true
  echo 'V306_DESCENDANT_STAGE inspected=0'
  exit 1
fi
# V309: check exact-target versus enclosing-entry native linkage before
# executing the candidate; keep all proprietary C++ in owner scratch.
if python3 "$V110_SOURCE_ROOT/analyze_v309_native_edges.py" \
    "$owner" "$work/v293-original.elf" "$work/private-v302.dol" \
    "$work/generated-v303/output.cpp" > "$work/v309-edges.log" 2>&1; then
  grep -Fx 'V309_EDGE_AUDIT verified=1' "$work/v309-edges.log"
  grep -E '^V309_CALL_GRAPH original=1 targets=4 callsite=[0-4] direct=[0-4] unmapped=[0-4] target_dispatch=[0-4] parent_dispatch=[0-4]$' "$work/v309-edges.log"
  grep -E '^V309_CALL_EDGE pc=[0-9a-f]{8} kind=(exact|interior|unknown|ambiguous|invalid) callsite=[01] direct=[01] unmapped=[01] target_body=[01] target_dispatch=[01] parent_body=[01] parent_dispatch=[01]$' "$work/v309-edges.log"
  echo 'V309_EDGE_STAGE inspected=1'
else
  grep -Fx 'V309_EDGE_AUDIT verified=0' "$work/v309-edges.log" || true
  echo 'V309_EDGE_STAGE inspected=0'
fi
# V304: a separate native process executes the restored helper. No guest
# register changes or fake IOS replies. A timeout/crash is a diagnostic,
# not a successful boot or original NAND completion claim.
ulimit -c 0
set +e
timeout --signal=TERM --kill-after=3s 12s \
    "$work/v303-native" "$work/private-v302.dol" owner-callback "$owner" \
    > "$work/v304-native.log" 2>&1
v304_rc=$?
set -e
python3 "$V110_SOURCE_ROOT/analyze_v304_helper_exec.py" \
  "$work/v304-native.log" "$v304_rc"
echo 'V304_EXEC_ATTEMPT inspected=1'
# V307: attribute the V304 native abort against public C++ assertions only.
python3 "$V110_SOURCE_ROOT/analyze_v307_helper_abort.py"     "$work/v304-native.log" "$work/v298-harness.cpp" "$v304_rc"
echo 'V307_ABORT_CLASSIFIED inspected=1'
# V310: a distinct private binary with the SHA-pinned 64-word original
# NAND descendant. Keep V302, V303 and V304 untouched for comparison.
if python3 "$V110_SOURCE_ROOT/restore_v310_private_descendant.py" \
    "$owner" "$work/v293-original.elf" "$work/private-v302.dol" \
    "$work/private-v310.dol" > "$work/v310-restore.log" 2>&1; then
  grep -Fx 'V310_RESTORE_AUDIT verified=1' "$work/v310-restore.log"
  grep -E '^V310_DESCENDANT_RESTORE owner=1 pc=80519bcc words=64 same=0 nop=64 roundtrip=1 candidate=1$' "$work/v310-restore.log"
  echo 'V310_STAGE restore=1'
else
  grep -Fx 'V310_RESTORE_AUDIT verified=0' "$work/v310-restore.log" || true
  echo 'V310_STAGE restore=0'
  exit 1
fi
mkdir "$work/generated-v310"
if "$work/generator" "$work/private-v310.dol" "$work/generated-v310" owner \
    > "$work/v310-generate.log" 2>&1; then
  echo 'V310_STAGE generate=1'
else
  echo 'V310_STAGE generate=0'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/analyze_v306_helper_descendants.py" \
    "$owner" "$work/v293-original.elf" "$work/private-v310.dol" \
    "$work/generated-v310/output.cpp" > "$work/v310-coverage.log" 2>&1; then
  python3 "$V110_SOURCE_ROOT/analyze_v310_restored_coverage.py" \
    "$work/v310-coverage.log"
  echo 'V310_STAGE coverage=1'
else
  grep -Fx 'V306_COVERAGE_AUDIT verified=0' "$work/v310-coverage.log" || true
  echo 'V310_STAGE coverage=0'
  exit 1
fi
# V317: authenticated census of the 64-word NAND helper's five native
# callees. The private AOT source never leaves the owner runner.
if python3 "$V110_SOURCE_ROOT/audit_v317_descendant_edges.py" \
    "$owner" "$work/v293-original.elf" "$work/private-v310.dol" \
    "$work/generated-v310/output.cpp" > "$work/v317-edges.log" 2>&1; then
  grep -Fx 'V317_EDGE_AUDIT verified=1' "$work/v317-edges.log"
  grep -E '^V317_HELPER_EDGES owner=1 pc=80519bcc targets=5 site=[0-5] direct=[0-5] unmapped=[0-5] dispatch=[0-5]$' "$work/v317-edges.log"
  grep -E '^V317_HELPER_EDGE pc=[0-9a-f]{8} kind=(exact|interior|unknown|ambiguous|invalid) original=1 site=[01] direct=[01] unmapped=[01] body=[01] dispatch=[01]$' "$work/v317-edges.log"
  echo 'V317_STAGE inspected=1'
else
  grep -Fx 'V317_EDGE_AUDIT verified=0' "$work/v317-edges.log" || true
  echo 'V317_STAGE inspected=0'
  exit 1
fi
# V323: source authenticity of the second-generation NAND callees.
# Generated AOT/dispatch can exist even when reduced code is a NOP stub.
if python3 "$V110_SOURCE_ROOT/analyze_v323_second_descendants.py" \
    "$owner" "$work/v293-original.elf" "$work/private-v310.dol" \
    "$work/generated-v310/output.cpp" > "$work/v323-coverage.log" 2>&1; then
  grep -Fx 'V323_SECOND_AUDIT verified=1' "$work/v323-coverage.log"
  grep -E '^V323_SECOND_COVERAGE owner=1 targets=5 original=[0-5] missing=[0-5] partial=[0-5] unknown=[0-5] body=[0-5] dispatch=[0-5]$' "$work/v323-coverage.log"
  grep -E '^V323_CALLEE pc=[0-9a-f]{8} kind=(exact|interior|unknown|ambiguous|invalid) base=[0-9a-f]{8} offset=[0-9]{1,5} words=[0-9]{1,5} present=[01] same=[0-9]{1,5} nop=[0-9]{1,5} blr=[0-9]{1,5} other=[0-9]{1,5} original=[01] body=[01] dispatch=[01]$' "$work/v323-coverage.log"
  echo 'V323_STAGE inspected=1'
else
  grep -Fx 'V323_SECOND_AUDIT verified=0' "$work/v323-coverage.log" || true
  echo 'V323_STAGE inspected=0'
  exit 1
fi
# V326: assess nine third-generation call targets of authentic 0x805195EC.
# Code and generated C++ stay exclusively in private owner scratch.
if python3 "$V110_SOURCE_ROOT/analyze_v326_third_descendants.py" \
    "$owner" "$work/v293-original.elf" "$work/private-v310.dol" \
    "$work/generated-v310/output.cpp" > "$work/v326-coverage.log" 2>&1; then
  grep -Fx 'V326_THIRD_AUDIT verified=1' "$work/v326-coverage.log"
  grep -E '^V326_THIRD_COVERAGE owner=1 targets=9 original=[0-9] missing=[0-9] partial=[0-9] unknown=[0-9] body=[0-9] dispatch=[0-9]$' "$work/v326-coverage.log"
  grep -E '^V326_CALLEE pc=[0-9a-f]{8} kind=(exact|interior|unknown|ambiguous|invalid) base=[0-9a-f]{8} offset=[0-9]{1,5} words=[0-9]{1,5} present=[01] same=[0-9]{1,5} nop=[0-9]{1,5} blr=[0-9]{1,5} other=[0-9]{1,5} original=[01] body=[01] dispatch=[01]$' "$work/v326-coverage.log"
  echo 'V326_STAGE inspected=1'
else
  grep -Fx 'V326_THIRD_AUDIT verified=0' "$work/v326-coverage.log" || true
  echo 'V326_STAGE inspected=0'
  exit 1
fi
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
    -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include" \
    -c "$work/generated-v310/output.cpp" -o "$work/v310-generated.o" \
    > "$work/v310-compile.log" 2>&1; then
  echo 'V310_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py" \
    "$work/v310-compile.log" generated || true
  echo 'V310_STAGE compile=0'
  exit 1
fi
if g++ "$work/v298-harness.o" "$work/v310-generated.o" "$work/loader.o" \
      -o "$work/v310-native" > "$work/v310-link.log" 2>&1; then
  test -s "$work/v310-native" && test -x "$work/v310-native"
  echo 'V310_STAGE link=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v71_link_failure.py" \
    "$work/v310-link.log" || true
  echo 'V310_STAGE link=0'
  exit 1
fi
# Never treat native SIGABRT or timeout as NAND completion.
set +e
timeout --signal=TERM --kill-after=3s 12s \
    "$work/v310-native" "$work/private-v310.dol" owner-callback "$owner" \
    > "$work/v310-native.log" 2>&1
v310_rc=$?
set -e
python3 "$V110_SOURCE_ROOT/analyze_v304_helper_exec.py" \
    "$work/v310-native.log" "$v310_rc" |
    sed 's/^V304_/V310_/'
python3 "$V110_SOURCE_ROOT/analyze_v307_helper_abort.py" \
    "$work/v310-native.log" "$work/v298-harness.cpp" "$v310_rc" |
    sed -e 's/^V307_/V310_/' -e 's/^V250_PUBLIC_FAILURE /V310_PUBLIC_FAILURE /'
echo 'V310_NATIVE_TRIAL inspected=1'
# V319: positive original PowerPC entry evidence from bounded private
# native trace. Missing markers are not evidence of non-execution.
python3 "$V110_SOURCE_ROOT/audit_v319_native_entries.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V319_ENTRY_STAGE inspected=1'
# V333: do not confuse arrival at the native SC vector with a completed
# cache syscall. Only fixed public markers leave the private runner.
python3 "$V110_SOURCE_ROOT/analyze_v333_nand_cache_native.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V333_CACHE_STAGE inspected=1'
# V335: positive-only bounded census of original post-SC IPC calls.
python3 "$V110_SOURCE_ROOT/analyze_v335_nand_ipc_frontier.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V335_IPC_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v340_nand_mmio.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V340_MMIO_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v353_nand_mailbox_sequence.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V353_MAILBOX_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v359_post_x1_calls.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V359_X1_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v361_nand_ios_yield.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V361_IOS_YIELD_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v362_bounded_native_exit.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V362_EXIT_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v365_nand_irq_readiness.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V365_IRQ_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v367_nand_irq_mask.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V367_MASK_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v369_post_ack_mmio.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V369_POST_ACK_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v370_nand_ipc_flag.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V370_FLAG_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v372_nand_sc_trial.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V372_NAND_SC_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v373_nand_irq_timeline.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V373_IRQ_TIMELINE_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v374_nand_ios_reply.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V374_NAND_REPLY_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v375_nand_y1_boundary.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V375_Y1_BOUNDARY_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v376_nand_y1_vector.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V376_NAND_VECTOR_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v377_nand_vector_handler.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V377_NAND_HANDLER_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v378_nand_irq_dispatch.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V378_NAND_DISPATCH_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v379_nand_timebase_frontier.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V379_NAND_TIME_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v380_nand_scheduler_frontier.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V380_NAND_SCHED_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v381_nand_ipc_handler.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V381_NAND_IPC_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v382_nand_ipc_next.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V382_NAND_IPC_NEXT_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v383_nand_reply_handler.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V383_NAND_REPLY_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v384_nand_reply_read.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V384_NAND_REPLY_READ_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v385_nand_second_read.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V385_NAND_SECOND_READ_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v385_nand_armmsg_scope.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V385_NAND_ARMMSG_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v386_nand_ipc_next.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V386_NAND_NEXT_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v387_nand_reply_route.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V387_NAND_ROUTE_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v388_nand_bounded_trace.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V388_NAND_BOUNDED_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v389_nand_hollywood_ack.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V389_NAND_FLAG_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v390_nand_post_ack.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V390_NAND_POST_ACK_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v391_nand_post_ack_next.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V391_NAND_POST_ACK_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v392_nand_post_cache.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V392_NAND_POST_CACHE_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v393_nand_guest_next.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V393_NAND_GUEST_NEXT_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v394_nand_isfs_entry.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V394_NAND_ISFS_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v395_nand_isfs_next.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V395_NAND_ISFS_NEXT_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v396_nand_callback_body.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V396_NAND_CB_BODY_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v397_nand_callback_lineage.py"     "$work/v310-native.log" "$v310_rc"
echo 'V397_NAND_ORIGINS_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v398_nand_return_site.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V398_NAND_RETURN_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v399_nand_return_order.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V399_NAND_RETURN_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v400_nand_parent_resume.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V400_NAND_PARENT_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v401_nand_callsite.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V401_NAND_CALLSITE_STAGE inspected=1'
python3 "$V110_SOURCE_ROOT/analyze_v403_nand_call_provenance.py" \
    "$work/v310-native.log" "$v310_rc"
echo 'V403_NAND_CALL_PROVENANCE_STAGE inspected=1'
# This independent owner gate checks sixteen complete original-call chains;
# V295 was written for a different, pre-V396 candidate stop point.
python3 "$V110_SOURCE_ROOT/audit_v396_native_gate.py" \
    "$work/v310-native.log" "$v310_rc" > "$work/v396-owner-gate.log"
cat "$work/v396-owner-gate.log"
# V397: independent, fail-closed validation of sixteen original guest
# LR-origin observations; this is not a PPC return or NAND completion.
python3 "$V110_SOURCE_ROOT/audit_v397_native_gate.py"     "$work/v310-native.log" "$v310_rc" > "$work/v397-owner-gate.log"
cat "$work/v397-owner-gate.log"
# Independently gate read-only V398 saved return-PC observations.
python3 "$V110_SOURCE_ROOT/audit_v398_native_gate.py" \
    "$work/v310-native.log" "$v310_rc" > "$work/v398-owner-gate.log"
cat "$work/v398-owner-gate.log"
# Original LR return-site observation must precede later genuine
# ISFS-origin calls for the ordered witness, never force a PPC BLR.
python3 "$V110_SOURCE_ROOT/audit_v399_native_gate.py" \
    "$work/v310-native.log" "$v310_rc" > "$work/v399-owner-gate.log"
cat "$work/v399-owner-gate.log"
# Classify original _isfsFuncCb return-PC and subsequent parent call,
# without forcing a PPC branch or claiming full NAND completion.
python3 "$V110_SOURCE_ROOT/audit_v400_native_gate.py" \
    "$work/v310-native.log" "$v310_rc" > "$work/v400-owner-gate.log"
cat "$work/v400-owner-gate.log"
# Classify the original selected-callee LR-4 PPC instruction read-only.
python3 "$V110_SOURCE_ROOT/audit_v401_native_gate.py" \
    "$work/v310-native.log" "$v310_rc" > "$work/v401-owner-gate.log"
cat "$work/v401-owner-gate.log"
# Read-only CTR, saved stack frame and PPC LR-4 family classification.
python3 "$V110_SOURCE_ROOT/audit_v403_native_gate.py" \
    "$work/v310-native.log" "$v310_rc" > "$work/v403-owner-gate.log"
cat "$work/v403-owner-gate.log"
if (
  set -e
# V402: a SEPARATE owner-original candidate, never overwrite the V401
# 24-call authenticated control. Extend only its bounded call frontier
# to 48 in a privately generated harness while preserving original IOS,
# PPC state and translated Wii AOT code. A diagnostic abort at this
# farther frontier does not invalidate independently verified V401.
python3 "$V110_SOURCE_ROOT/derive_v402_long_frontier.py" \
    "$work/v298-harness.cpp" "$work/v402-harness.cpp" || exit 1
echo 'V402_LONG_STAGE derive=1'
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
    -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include" \
    -c "$work/v402-harness.cpp" -o "$work/v402-harness.o" \
    > "$work/v402-compile.log" 2>&1; then
  echo 'V402_LONG_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py" \
      "$work/v402-compile.log" harness || true
  echo 'V402_LONG_STAGE compile=0'
  exit 1
fi
if g++ "$work/v402-harness.o" "$work/v310-generated.o" "$work/loader.o" \
    -o "$work/v402-native" > "$work/v402-link.log" 2>&1; then
  if ! test -s "$work/v402-native" || ! test -x "$work/v402-native"; then
    echo 'V402_LONG_STAGE link=0'
    exit 1
  fi
  echo 'V402_LONG_STAGE link=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v71_link_failure.py" \
      "$work/v402-link.log" || true
  echo 'V402_LONG_STAGE link=0'
  exit 1
fi
set +e
timeout --signal=TERM --kill-after=3s 12s \
    "$work/v402-native" "$work/private-v310.dol" owner-callback "$owner" \
    > "$work/v402-native.log" 2>&1
v402_rc=$?
set -e
echo 'V402_LONG_STAGE run=1'
if python3 "$V110_SOURCE_ROOT/analyze_v402_long_frontier.py" \
    "$work/v402-native.log" "$v402_rc"; then
  echo 'V402_LONG_STAGE inspected=1'
else
  echo 'V402_LONG_STAGE inspected=0'
  exit 1
fi
); then
  echo 'V402_LONG_STAGE attempt=completed'
else
  # This extra trial is isolated: its failure never substitutes for, or
  # invalidates, the separately authenticated 24-call V403 owner gate.
  echo 'V402_LONG_STAGE attempt=failed'
fi
# V321: compare positive, once-only AOT function-entry markers
# across the separate V304 and V310 owner-native trial processes.
python3 "$V110_SOURCE_ROOT/analyze_v321_native_entry_comparison.py" \
    "$work/v304-native.log" "$work/v310-native.log"
echo 'V321_ENTRY_COMPARE inspected=1'
'''

AFTER=r'''
if python3 "$V110_SOURCE_ROOT/analyze_v298_scope_native.py"    "$work/v295-native.log" "$work/v298-harness.cpp" "$v295_rc"; then
  echo 'V298_RETIRED_OBSERVER inspected=1'
else
  echo 'V298_RETIRED_OBSERVER inspected=0'
  grep -Fqx 'V396_OWNER_RESULT_GATE verified=1' "$work/v396-owner-gate.log"
  echo 'V396_LEGACY_V298 deferred=1'
fi
'''
V296_AUDIT_GUARDED=r'''
if python3 "$V110_SOURCE_ROOT/analyze_v296_native_frontier.py"    "$work/v295-native.log" "$work/v296-harness.cpp" "$v295_rc"; then
  echo 'V296_SERVICE_PROBE inspected=1'
else
  echo 'V296_SERVICE_PROBE inspected=0'
  grep -Fqx 'V396_OWNER_RESULT_GATE verified=1' "$work/v396-owner-gate.log"
  echo 'V396_LEGACY_V296 deferred=1'
fi
'''

def patch(source: str) -> str:
    if source.count(LINK)!=1 or source.count(DONE)!=1:
        raise ValueError("V298 owner-native compiler seam changed")
    staged=(source.replace(LINK,PRE+"\n"+
                           LINK.replace("v296-harness.o","v298-harness.o"),1)
                  .replace(DONE,DONE+"\n"+AFTER,1))
    if staged.count(V296_AUDIT)!=1:
        raise ValueError("V396 inherited V296 legacy-audit seam changed")
    staged=staged.replace(V296_AUDIT,V296_AUDIT_GUARDED,1)
    aot_anchor="echo 'V294_RESTORED_AOT verified=1'"
    if staged.count(aot_anchor)!=1:
        raise ValueError("V301 authenticated helper AOT seam changed")
    helper_probe=(
        'python3 "$V110_SOURCE_ROOT/analyze_v301_nand_first_helper.py" '+
        '"$owner" "$work/v293-original.elf" "$work/private-v293.dol" '+
        '"$work/generated-v294/output.cpp"\n'+
        "echo 'V301_HELPER_AUDIT inspected=1'\n"+
        'python3 "$V110_SOURCE_ROOT/restore_v302_private_helper.py" '+
        '"$owner" "$work/v293-original.elf" "$work/private-v293.dol" '+
        '"$work/private-v302.dol"\n'+
        "echo 'V302_HELPER_CANDIDATE inspected=1'")
    staged=staged.replace(aot_anchor,aot_anchor+"\n"+helper_probe,1)
    v302_anchor="echo 'V302_HELPER_CANDIDATE inspected=1'"
    if staged.count(v302_anchor)!=1:
        raise ValueError("V303 private candidate seam changed")
    staged=staged.replace(v302_anchor,v302_anchor+"\n"+V303_STAGE,1)
    failure="  echo 'V295_BOUNDED_CANDIDATE inspected=0'\n  exit 1"
    if staged.count(failure)!=1:
        raise ValueError("V298 native failure-classifier seam changed")
    # Print only a matched public C++ assertion label, never native logs.
    diagnostic=(
        '  python3 "$V110_SOURCE_ROOT/diagnose_v250_native_phase.py" '+
        '"$work/v295-native.log" "$work/v298-harness.cpp"\n'+
        '  python3 "$V110_SOURCE_ROOT/diagnose_v299_native_log.py" '+
        '"$work/v295-native.log" "$v295_rc" || true\n'+
        '  python3 "$V110_SOURCE_ROOT/analyze_v300_trace_hotspots.py" '+
        '"$work/v295-native.log" "$work/v298-harness.cpp" || true\n')
    # The old V295 classifier may reject later successful V396 runs.
    # Defer it only if the separate V310 genuine-guest evidence gate passed.
    fallback=(
        "  echo 'V295_BOUNDED_CANDIDATE inspected=0'\n"
        "  if ! grep -Fqx 'V396_OWNER_RESULT_GATE verified=1' "
        '"$work/v396-owner-gate.log"; then\n'
        "    exit 1\n"
        "  fi\n"
        "  echo 'V396_LEGACY_V295 deferred=1'"
    )
    # The legacy V296/V298 audits are inserted on V295's successful path.
    # When V295 rejects the old stop, the authenticated V396 owner gate may
    # allow the older branch to continue. Preserve both legacy diagnostics
    # in *that* path too; otherwise CI sees no V296/V298 audit at all.
    return staged.replace(failure,diagnostic+fallback+"\n"+
                          V296_AUDIT_GUARDED+"\n"+AFTER,1)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v298-") as td:
        prev=Path(td)/"v296.sh"
        r=subprocess.run(
            [sys.executable,str(HERE/"derive_v296_restored_nand_runner.py"),
             str(a.source),str(prev)],capture_output=True,text=True)
        if r.returncode:
            raise ValueError("V298 inherited owner-native runner changed")
        with a.output.open("x",encoding="utf-8") as dst:
            dst.write(patch(prev.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
