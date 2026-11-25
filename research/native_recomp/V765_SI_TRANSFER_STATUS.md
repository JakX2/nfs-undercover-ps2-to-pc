# V765: actual original __SITransfer focused device execution

The original V529 discovery witness establishes the actual SI global structure and channel/command/input/callback arguments. V765 composes the exact 108-word root, six-register compiler save/restore aliases and original interrupt-control leaves. In both generated modes, test four idle channel requests following a real prior W1C and four busy cases. Route only original native word load/store instructions to the real SI controller, verify request token and explicit absent endpoint through V750, and refuse a corrupted PI mask. Verify guest SI state, ABI and no fallback. Synthetic initial RAM and a focused post-ACK device fixture, not full startup or a live handler call. Private execution pending; fixture assumptions about the busy path and actual MMIO count require confirmation.

## V766 native post-return timing

Replace the host-side post-return tick loop with 16 independently authored translated NOPs after the original transfer return. All completion ticks now occur at actual generated native instruction labels, including the synthetic caller continuation. The original return and guest state are still verified at the first caller label. Require all 16 labels, unchanged ABI/result, correct completion and PI state at the last label; busy cases must remain quiescent. No claim that these synthetic caller instructions belong to original startup. Private rerun pending.

## V770 compilation correction

V769 independently reproduced the POSIX `access` function name collision in the independently authored harness. Rename the local state to `mmio_accessed`. Keep `-Werror` on the harness and compile generated units separately with only `type-limits` nonfatal; the prior private compiler census classified one generated comparison diagnostic but did not identify its exact warning. Extend the redacted diagnostic with an allowlisted warning flag category to confirm the actual warning. Sanitizers and all native route/semantic checks remain enabled. Private execution pending.
