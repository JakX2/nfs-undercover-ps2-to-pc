# V450: Windows extended original OSInit startup scopes

The authenticated Windows V441 owner run 45320085353 already verified
original OSInit time initialization with the strict loader and corrected
native instruction visits. The V443 owner Linux run translated and linked
the hardware continuation and passed nine canonical checkpoints before
a zero-exit audit mismatch (V449 formatting candidate). No later Windows
checkpoint has yet been authenticated.

Extend the Windows contract to os-hardware, os-arena and os-ipc, sharing
the same source-backed patches and observers as the Linux lanes. V443
function-root identity precedes hardware state patches; V29 performance
SPR support is installed before V18/V20 and its composition is checked
before V30 HID4/FPSCR. V445 exact dispatch is included in os-ipc only.
The existing native tick and strict loader controls are retained.

The default Windows owner scope advances to os-hardware; os-time remains
a selectable authenticated control. Both arena scopes are manual
candidates. The synthetic build remains startup-only. Expanded source
tests cover all nine scopes, all cross-scope log pairings, Windows exit
codes, duplicate or missing results, unknown markers, optional copy and
hexadecimal stage rejection. The owner workflow still cleans original
files, generated C++ and the linked executable; no game boot claimed.
