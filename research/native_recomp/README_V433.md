# V433: complete-image DBInit and OSInit entry candidate

This is an opt-in continuation of V430, not an original-game result yet.
The complete native image must first pass the unchanged V430 data witness,
then execute the original post-data startup instructions, DBInit and the
original call to OSInit. The latter is the bounded observation endpoint:
the OSInit body, main, first frame and gameplay are not proven.

Unlike the old V24 sliced fixture, the pinned full host initializes
low-memory arena-high at 0x80000034. The witness does not overwrite this
field, boot-info at 0x800000F4, or any guest memory. Their presence is
reported only as two booleans. Unexpected intervening native calls fail
closed rather than being silently skipped. This can identify a different
boot route without forcing the synthetic ordinary-boot path.

The owner SHA, both original linked branch callsites, DBInit return
geometry, generated entry trace seams and original guest entry words
are validated. At OSInit entry, the witness checks the original DBInit
debug pointer, base, initialized flag, startup low-memory clear, stack
pointer and small-data registers. The interpreter remains rejected.
No original instructions, assets, private expectation headers or generated
game translations are committed.

Source-only C++ witness: four boot-metadata combinations, 44 negative
controls and four duplicate-stop controls, verified locally with strict
C++20, ASan and UBSan. The separate Python preparation and audit suite
runs in CI. The new full-image scope is `os-entry`; the independent
`data` scope remains unchanged. Authentication of the owner execution
is required before marking this milestone complete.
