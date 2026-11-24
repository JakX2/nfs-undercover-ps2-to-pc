# V446: complete-image MEM2 and IPC-buffer initialization candidate

V445 pinned workflow 45321139346 passed both split and non-split sparse
dispatch regressions and both 14/14 host-runtime suites. The corrected
native dispatch had no interpreter fallback in its synthetic regression.

The manual os-ipc scope extends V444 through both original MEM2 setters,
the original IPC-buffer pointer copy and actual OSExceptionInit entry
(before its body). Four authentic call edges are required. V37/V38
source validators are reused. The complete-image lane requires ordered,
non-overlapping runtime MEM2 and IPC bounds; it checks the original low
clamp, input preservation, exact global stores, adjacent guards and ABI.
No guest code or metadata is replaced. Local GCC C++20 ASan/UBSan:
four valid configurations, 56 negative controls and duplicate stops.

Only os-ipc also enables the independently verified V445 dispatcher
and V438 tick corrections. Other scopes remain independent controls.
Source tests run in regular CI. Owner integration is pending. This
is pointer setup, not IOS communication, OSInit completion or boot.
No original-game material is committed.
