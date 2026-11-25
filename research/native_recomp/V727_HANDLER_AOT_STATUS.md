# V727: generated handler-return integration control

Extends the independently authored V710 fixture with an actual PPC bctrl dispatcher, LR-save/restore handler prologue/epilogue, and a post-helper SI status store. Uses the production V726 capture, return, poll and resume hooks. Both split and non-split generated modes must preserve the four older stop/refusal lanes, complete the genuine native indirect return, and reject a synthetic corrupted saved LR. No original code in fixture. Tests pending CI.
