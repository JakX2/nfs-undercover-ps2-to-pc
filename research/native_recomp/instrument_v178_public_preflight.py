#!/usr/bin/env python3
"""Insert privacy-safe V178 preflight breadcrumbs into the derived public runner.

Scope: only the public run_v79 shell's source-only runtime/cache/analyzer
steps, *before* private DOL fixture construction. Every requested anchor
must be unique; no shell command argument is changed or bypassed.
Markers contain allowlisted step names, never an owner path, log, or bytes.
"""
from __future__ import annotations

STEPS=(
    ("runtime_verify", 'python3 "$here/verify_perf_combo_v29.py" "$root"'),
    ("cache_verify", 'python3 - "$root" "$here" > "$work/verify-cache.log"'),
    ("exi_compile", 'g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_exi_id_device_v56.cpp"'),
    ("exi_test", '"$work/exi-device-test"'),
    ("jump_patch", 'python3 "$here/test_jump_table_patch_v58.py"'),
    ("jump_test", '"$work/jump-table-test"'),
    ("tail_roots", 'python3 "$here/apply_explicit_tail_roots_v71.py" "$root" --strict-native'),
    ("backward_tails", 'python3 "$here/apply_explicit_backward_tails_v76.py" "$root"'),
    ("tail_test", '"$work/tail-root-test"'),
    ("sram_compile", 'g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_exi_sram_device_v60.cpp"'),
    ("sram_test", '"$work/sram-device-test"'),
    ("hollywood_test", '"$work/hollywood-mmio-test"'),
    ("vector_test", '"$work/sc-vector-test"'),
    ("lowmem_patch", 'python3 "$here/test_native_lowmem_patch_v63.py"'),
    ("dsp_test", '"$work/dsp-device-test"'),
    ("bat_test", '"$work/bat-test"'),
    ("dcbz_patch", 'python3 "$here/test_dcbz_patch_v67.py"'),
    ("dcbz_test", '"$work/dcbz-test"'),
)

# Optional milestones after the public-only preflight. The older runner
# may have rewritten a command; absence never bypasses any execution.
PHASES=(
    ("fixture_make", 'python3 "$here/make_start_to_ipc_ack_v77.py" "$owner" "$work/private.dol"'),
    ("fixture_geometry", 'python3 "$here/test_v77_continuous_ipc_ack_geometry.py" "$work/private.dol" "$owner"'),
    ("generator_compile", 'g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable'),
    ("generation", '"$work/generator" "$work/private.dol" "$work/generated" owner'),
    ("native_compile", 'for unit in harness generated loader; do'),
    ("native_test", '"$work/native" "$work/private.dol" owner "$owner"'),
)

def derive(script: str)->str:
    if "V178_PREFLIGHT enter=" in script:
        raise ValueError("V178 breadcrumbs already applied")
    for step,command in STEPS:
        # Only insert at an exact shell command starting at a line boundary.
        # Source-only command arguments stay unchanged.
        lines=script.splitlines(keepends=True)
        hits=[i for i,line in enumerate(lines) if line.startswith(command)]
        if len(hits)!=1:
            raise ValueError(f"V178 public preflight command {step} count={len(hits)}")
        at=hits[0]
        lines.insert(at, f"echo 'V178_PREFLIGHT enter={step}'\n")
        script="".join(lines)
    lines=script.splitlines(keepends=True)
    final=[i for i,line in enumerate(lines) if line.startswith('"$work/dcbz-test"')]
    if len(final)!=1:
        raise ValueError("V178 final public preflight executable count differs")
    lines.insert(final[0]+1,"echo 'V178_PREFLIGHT complete=dcbz_test'\n")
    script="".join(lines)
    for phase,command in PHASES:
        lines=script.splitlines(keepends=True)
        hits=[i for i,line in enumerate(lines) if line.startswith(command)]
        if len(hits)>1:
            raise ValueError(f"V178 optional public pipeline command {phase} ambiguous")
        if hits:
            lines.insert(hits[0],f"echo 'V178_PIPELINE enter={phase}'\n")
            script="".join(lines)
    return script
