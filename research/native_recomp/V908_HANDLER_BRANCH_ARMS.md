# V908: original handler branch arm continuations

V907 private job 139159642067 identified five original fallthrough words (one load) and three taken-arm words, both followed by further conditional branches. V908 executes the original words on each arm, verifies the extra mapped load against guest bytes, and stops before each subsequent branch. The first 14 instructions retain the V906 GPR oracle; the extra arm integer operations are covered by original-code identity and native label continuity, not a full arithmetic oracle. No new MMIO authorization. Pending private execution.
