#!/usr/bin/env python3
"""Privacy-safe V178 owner runner stage classifier, never echoes private data.

The owner job captures stdout/stderr in a private, deleted log. This utility
reads it, reports only an allowlisted stage and failure category. It never
prints lines, paths, addresses, messages or generated source from that log.
"""
import argparse
import re
from pathlib import Path

STAGES=(
    "runtime_cache_trace_verified",
    "fixture_generated",
    "geometry_verified",
    "generator_compiled",
    "generation_complete",
    "native_compiled",
    "native_test_passed",
)
SAFE_REASONS=(
    ("verify_runtime", ("V71 inherited performance/HID4 runtime invalid",)),

    ("analyzer_compile", (
        "V72 original-free jump-table analyzer test compile failed",
        "V72 original-free tail-root analyzer compile failed",
    )),
    ("fixture", ("V71 fixture construction failed", "V71 STM geometry guard failed")),
    ("generator_compile", ("V73 generator compilation failed",)),
    ("generator_runtime", ("V72 original PPC generator guards failed",)),
    ("native_compile", ("V72 original translated native compilation failed",)),
    ("native_assertion", ("V67_NATIVE_ASSERTION id=", "V71_NATIVE_ASSERTION id=")),
    ("python_error", ("Traceback (most recent call last):",)),
    ("unexpected_exit", ("Segmentation fault", "Aborted", "Killed", "Terminated")),
)

# Exact allowlisted *public test script basenames* only. The classifier
# deliberately never includes a private traceback filename in output.
PREFLIGHT_SCRIPTS=(
    "verify_perf_combo_v29.py",
    "apply_cache_events_v43.py",
    "apply_cache_trace_v44.py",
    "test_jump_table_patch_v58.py",
    "apply_explicit_tail_roots_v71.py",
    "apply_explicit_backward_tails_v76.py",
    "test_native_lowmem_patch_v63.py",
    "test_dcbz_patch_v67.py",
    "derive_v178_sc_reply_burst_harness.py",
)

def classify(data: str)->str:
    if len(data)>25_000_000:
        raise ValueError("owner output exceeds public classifier bound")
    # Use the last *completed* trusted stage marker, not a guessed milestone.
    phases=[s for s in STAGES if re.search(
        r"(?m)^V79_STAGE "+re.escape(s)+r"$",data)]
    if phases:
        stage=phases[-1]
    elif "V110_WRAPPER syntax_ok" in data:
        stage="runner_preflight"
    elif "V110_WRAPPER derived" in data:
        stage="runner_syntax"
    else:
        stage="wrapper"
    reason="unclassified"
    for name,strings in SAFE_REASONS:
        if any(s in data for s in strings):
            reason=name
            break
    script="none"
    if reason=="python_error":
        mentioned=[name for name in PREFLIGHT_SCRIPTS if name in data]
        if mentioned:
            script=mentioned[-1][:-3]
        elif stage=="runner_preflight":
            # Inspect only traceback references to checked-in PUBLIC
            # research scripts. Never echo any arbitrary/private file name.
            frames=re.findall(r'File "([^"]+)", line [0-9]{1,6}',data)
            allowed={p.name for p in Path(__file__).parent.glob("*.py")}
            hits=[]
            for frame in frames:
                base=Path(frame).name
                normalized=frame.replace(chr(92),"/")
                if ("/research/native_recomp/" in normalized and
                    base in allowed and base.endswith(".py")):
                    hits.append(base)
            if hits:
                script=hits[-1][:-3]
            else:
                # V79 also runs a small inline source-only cache check.
                lines=re.findall(r'File "<stdin>", line ([0-9]{1,3})',data)
                if lines and 1<=int(lines[-1])<=40:
                    script="inline_cache_line_"+str(int(lines[-1]))
    return f"V178_FAILURE_STAGE phase={stage} reason={reason} script={script}"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("log",type=Path)
    a=p.parse_args()
    # Read only the owner's bounded local CI log; this file is never uploaded.
    print(classify(a.log.read_text(encoding="utf-8",errors="replace")))

if __name__=="__main__":
    main()
