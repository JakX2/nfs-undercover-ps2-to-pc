# V983: maintain memory witness at refused suffix boundary

All non-call/return boundaries selected by V982 must have been replaced by a private nonexecuted BLR guard. Apply the same pending-store and exact-tick memory check to that boundary, rather than bypass the guard for census output. Add seven synthetic controls covering explicit wider-label opt-in, default-limit refusal, oversized/invalid limits, corrupted labels, pending store corruption and skipped native tick. No original boundary is executed. Pending CI.
