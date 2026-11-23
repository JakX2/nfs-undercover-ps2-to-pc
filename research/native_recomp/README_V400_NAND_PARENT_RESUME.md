# Undercover Wii NAND return progression: V398-V400

## Evidence boundaries

V392-V395 (authenticated NAND original-guest execution) and V396-V397
(16 complete bounded call lineages) are verified. The V398 authenticated
owner run (workflow 45272006977, 2026-11-23) also established 16/16 clean
observations of the saved LR in the original guest PC during callback
dispatch: `site_any=1 mapped_any=1 before_cap_any=1`, with up to 22
callback-boundary samples. Those are *aggregate* flags and do not establish
that every individual trial resumed, or that a specific PPC `blr` was
executed. V398's old 24-call bound remains unchanged.

V399 checks **per-trial chronology**: a natural saved-PC witness followed
by a genuine ISFS-origin guest call. It also checks the original PPC
`bcctr`-with-link opcode at the callsite (read-only, boolean result only).
V400 extends classification to the original `_isfsFuncCb` caller LR
(`0x805192AC`) and its later parent-origin guest calls. Neither V399 nor
V400 may force a return, change PPC state, or synthesize IOS/NAND output.

A result with `ordered_all=0` is a valid census, **not** proof that the
return or ordered guest continuation was reached. Original guest branches,
native callback return, complete boot, title screen, and gameplay remain
independent, unverified milestones until their specific evidence passes.

## Tests and privacy

Run the original-free regression suite using:

```sh
python3 -m unittest discover -s research/native_recomp -p 'test_v398*.py' -v
python3 -m unittest discover -s research/native_recomp -p 'test_v399*.py' -v
python3 -m unittest discover -s research/native_recomp -p 'test_v400*.py' -v
```

The owner runner separately recompiles and executes only authenticated
private Wii resources in temporary CI storage. Public CI prints bounded
bit fields, counts, and gate results only. It does not print guest opcodes,
register values, user-provided NAND data, or generated copyrighted code.
Legacy V295-V298 classifications are retained for diagnosis but cannot
replace the original V396-V400 proof gates.
