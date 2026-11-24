# V445: exact native dispatch coverage and entry priority

This independent original-free compiler candidate addresses two closely
related dispatcher bugs found while reviewing V443. Both output modes
currently generate broad min/max fallback bounds even when a function
contains sparse reachable labels, and emit entry and resume cases in one
pass. A lower root's back-edge can steal a higher root's entry switch case.

The patch replaces each broad bound with contiguous runs of actual
emitted instruction addresses, refuses unaligned fallback dispatch, and
allows resume cases only for emitted labels which are not independently
analyzed roots. Exact roots therefore retain priority, including HLE
roots. This does not change guest instructions, register state, or the
existing policy for unknown dispatch. It preserves deterministic
first-match behavior for legitimately shared labels.

The new pinned AOT test uses three synthetic roots, a sparse function
crossing a different function's interior, and a backward edge at the
higher exact root. It compares baseline and corrected run_game execution
in both modes (after the already verified V443 root identity patch).
The old path is expected to fall into the interpreter on a known interior
label and omit the higher root trace. The corrected path must return the
same guest register values without that fallback and with the exact trace.

This is a separate CI candidate; it is not enabled in the owner image.
No gameplay, boot or performance claims are implied.
