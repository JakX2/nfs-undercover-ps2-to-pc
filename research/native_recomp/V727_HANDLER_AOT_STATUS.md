# V727: generated handler-return integration control

Extends the independently authored V710 fixture with an actual PPC bctrl dispatcher, LR-save/restore handler prologue/epilogue, and a post-helper SI status store. Uses the production V726 capture, return, poll and resume hooks. Both split and non-split generated modes must preserve the four older stop/refusal lanes, complete the genuine native indirect return, and reject a synthetic corrupted saved LR. No original code in fixture. Tests pending CI.

## V729

V727 initially refused the synthetic generated resume label. The private route still fails closed; add bounded label/comment/tick classification and an exact public synthetic patch test. The synthetic-only runner may print its independently authored generated function on failure. V728's generic CFG census no longer calls the stricter full-handler shape gate (which requires four words and a store); original input authentication still invokes the full handler geometry gate.

## V733 fixture placement correction

The pinned upstream emitter deliberately emits interpreter-only bodies for roots below physical 0x3100. V727 had placed its independent dispatcher at 0x80003000, inside that reserved low-memory window. Move only the synthetic dispatcher to 0x8000b000. The original dispatcher is not in the low-memory window; its V726 installer already passed owner preflight. Do not alter upstream low-memory behavior or loosen native coverage.
