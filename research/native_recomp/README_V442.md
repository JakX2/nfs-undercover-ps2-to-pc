# V442: publish only safe restored-frame result aggregates

The V437 owner workflow succeeded overall, but its outer log allowlist
only published V432 and older markers. Consequently there is no public
evidence of the V437 attempt's outcome. This patch fixes the outer
allowlist and checks exactly the independent attempt status, either
a completed inspection or a categorized early failure. The output
contains only bounded aggregate counts and fixed stage/category names.
No raw guest address, instruction word, private log or game content is
published. A successful inspection is not a native return or boot claim.
