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
    ("preflight_done", "echo 'V79_STAGE runtime_cache_trace_verified'"),
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
    return script
