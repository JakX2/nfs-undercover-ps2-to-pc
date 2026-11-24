# V449: canonical decimal startup witness records

The authenticated V443 owner build 45320371327 passed unique trace
preparation, 113/113 syntax checks and native Linux link. It returned
zero with V439 hardware census stages=9, matched=9, copy=0, fallback=0,
reason=0, verified=0. No full hardware milestone is claimed from that
result. A strong possible explanation is the upstream runtime's shared
std::cout hexadecimal format: stages 10 through 13 become a through d.
The private run log was cleaned by the previous workflow.

The entire composed hardware observer now scopes numeric stream
formatting to canonical decimal, restoring the caller's flags and width
on return. No CPU state or guest instructions change. The existing
auditor still requires the exact decimal sequence and zero exit. It
additionally reports whether the terminal marker occurred exactly once
and whether the exact legacy hexadecimal sequence would explain the
cutoff. That diagnostic does not satisfy the canonical success gate.

The new C++ regression reproduces the legacy cutoff and checks eight
inherited stream formats; the Python test rejects incomplete, duplicated
or failed hex traces. A new authenticated owner run is needed to establish
whether the original hardware continuation actually completed.
