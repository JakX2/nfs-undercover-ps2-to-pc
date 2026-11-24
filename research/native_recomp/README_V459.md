# V459: restore the observed nested NAND NOP instead of the assumed last entry

Authenticated V452 run 45323588978 reproduced the five unique entries
with four original and one NOP. Its V447 plan rejected coverage at
ordinal 3. V447 incorrectly assumed the aggregate's sole NOP was the
last entry. V459 derives the target from the ordered private coverage
classification. The first two original frame entries remain mandatory;
exactly one NOP is eligible, with the same bounded original ELF span,
AOT body/dispatch proof, complete original bytes and reverse roundtrip.

Only the old entry prefix THROUGH the restored call must be reproduced
by the new run. Later control flow may legitimately change when the
real code replaces a NOP. No callback return, guest-state success or
boot is inferred from that prefix. The original V437 frame-return
checks and guards remain unchanged.

Synthetic regressions exercise all three eligible ordinals, changed
suffixes, and refusal to replace the first two authenticated frame
entries. Authenticated rerun pending.
