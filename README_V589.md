# V589: repair MI register backing state declaration

The V587 compiler caught an omitted private-state insertion: the existing AI control/status declaration uses uint32_t. Correct the exact seam, preserving AI state types. The workflow now also triggers on both underlying IRQ-bank headers. Retest pending; no MI native execution claim.
