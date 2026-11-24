# V443: preserve the actual function entry across backwards tail branches

V440 authenticated owner preparation (45320033791) localized the V439
failure to trace_duplicate ordinal=13, the optional memcpy helper.
The other twelve required traces passed. Pinned upstream analysis uses
the lowest visited PC as Function.start_address, even if the discovered
root is higher and branches backwards. Its emitter uses that same
field for trace identity. This can emit duplicate traces for the lower
entry and omit the actual higher entry trace. It can also misidentify
roots for lookup-based logic.

The new source-only patch stores the actual discovered function root
as start_address, and independently selects the lowest emitted label
for the generated initial fallthrough/switch. Existing instructions,
tail branches, resume cases and symbol map keys are preserved.
The synthetic regression exercises a backward tail branch to a lower
function, checks the unchanged four-instruction body, both root traces,
direct entry and two resumed PCs in actual pinned split/non-split AOT
executables before and after the patch. It rejects mixed or ambiguous
source layout. The owner candidate still requires the exact unique
V439 trace sites; no observer condition is relaxed.

The new patch is applied only in the os-hardware scope after the
independent pinned original-free regression passes. Existing complete
image checkpoints are unchanged. Original owner integration is pending.
