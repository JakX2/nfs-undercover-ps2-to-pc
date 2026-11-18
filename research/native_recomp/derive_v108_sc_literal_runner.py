#!/usr/bin/env python3
"""Derive V108 owner-authenticated initialized SC literal fixture from V107 runner."""
from derive_v107_sc_source_runner import derive as previous
def derive(source):
    s=previous(source)
    old="derive_v107_sc_source_probe_harness.py"
    if s.count(old)!=1:raise ValueError("V108 original path restoration hook absent")
    s=s.replace(old,"derive_v108_sc_literal_restore_harness.py",1)
    marker="^V107_SC_SOURCE mapped=[01] empty=[01] original_literal=[01]$"
    if s.count(marker)!=2:raise ValueError("V108 original provenance relay missing")
    more="|^V108_SC_GATE owner=[01] empty=[01] span=[01]$|^V108_SC_RESTORE owner=[01] empty_before=[01] exact=[01]$"
    return s.replace(marker,marker+more)
