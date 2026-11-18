#!/usr/bin/env python3
"""Derive read-only V107 provenance observer from the existing V104 build."""
from derive_v104_sc_async_submit_runner import derive as previous
def derive(source):
    s=previous(source)
    old="derive_v104_sc_async_submit_harness.py"
    if s.count(old)!=1:raise ValueError("V107 runner original source anchor missing")
    s=s.replace(old,"derive_v107_sc_source_probe_harness.py",1)
    marker="^V104_ASYNC_SAVE route=[01]$"
    if s.count(marker)!=2:raise ValueError("V107 bounded diagnostic relay missing")
    return s.replace(marker,marker+"|^V107_SC_SOURCE mapped=[01] empty=[01] original_literal=[01]$")
