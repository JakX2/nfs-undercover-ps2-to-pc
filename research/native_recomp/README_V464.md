# V464: authenticate and restore the newly reached missing NAND extent

V459 owner run 45325503307 restored the actual 58-word original
function, reached the 192-call guard, and found six unique entries,
five original and one missing. The original callback frame did not
return. V464 reproduces that exact control and re-authenticates V447
candidate and instrumentation before deriving the unique missing entry.

Only a bounded exact/interior original ELF extent is eligible. Any
mapped prefix must contain exact original words or NOPs, never a
modified service stub. Extension must satisfy the existing DOL
section, BSS, overlap and distance constraints. A reverse installation
and truncation proves complete previous DOL identity. Regenerated AOT
entry/dispatch and original frame hooks are required before execution.
The prior route must be reproduced through the repaired call, but not
after it. All original bytes and emitted code remain private.
Synthetic tests and owner CI pending; no completion claim.
