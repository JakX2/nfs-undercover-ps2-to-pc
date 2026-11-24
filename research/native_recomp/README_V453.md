# V453: authenticate the original debug dependency before exception setup

Earlier V46-V68 isolated tests used a synthetic DBPrintf return. That
substitution is not evidence that the original routine itself is a no-op.
The full-image path must execute the original code. V453 independently
authenticates all four known original exception debug callsites, reads
the exact ELF function extent and classifies its real body. Only a
bounded NOP/BLR leaf qualifies for the register-preserving native test;
a linked or otherwise nontrivial function is reported as unimplemented
in this lane, never replaced with a return. The true body is extracted
only to private scratch and never committed.

A separate original-free leaf control runs first in both actual pinned
NWiiRecomp output modes. The owner lane, if eligible, compiles and runs
the original instructions in both modes under ASan/UBSan, with four
independent register configurations per mode, original return LR,
instruction count, GPR/FPR/PS1 and control-register preservation and
zero interpreter fallback. The independent vector-table check verifies
the actual initialized DOL data table has non-overlapping cache-aligned
low-memory destinations and whether the syscall slot is present. It
prints only booleans, not the original offsets.

This short targeted workflow does not displace the queued full-image
runs. Both synthetic and owner results are pending CI. A successful
leaf result would remove a specific unresolved original exception
dependency, not prove full exception initialization or OS boot.
