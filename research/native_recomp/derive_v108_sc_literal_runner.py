#!/usr/bin/env python3
"""Derive V108 owner-authenticated initialized SC literal fixture from V107 runner."""
from derive_v107_sc_source_runner import derive as previous
def derive(source):
    s=previous(source)
    old="derive_v107_sc_source_probe_harness.py"
    if s.count(old)!=1:raise ValueError("V108 original path restoration hook absent")
    return s.replace(old,"derive_v108_sc_literal_restore_harness.py",1)
