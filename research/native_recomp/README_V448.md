# V448: select deepest changed complete-image scope and preserve preparation diagnostics

V441 authenticated Windows run 45320085353 passed all six original OS
time stages, strict loader equivalence and corrected ticks; exit zero,
no interpreter fallback. V445 pinned regression also passed.

V444/V446 now have explicit changed-source detection in the owner
workflow. The deepest changed scope is selected; unrelated source changes
still do not request a costly owner run. Manual scope remains authoritative.
The V443 original-free compiler regression gates both new scopes.

The V446 preparer now reports fixed category and stable helper ordinal
for missing or duplicate traces, source geometry and inherited arena
failures. Inherited V439 PreparationError retains its original safe
V440 marker. Eight synthetic trace-geometry controls are added. No
private exception strings, game bytes or logs are exposed. No prior
runtime assertion is relaxed.
