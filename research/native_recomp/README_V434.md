# V434: Windows complete-image continuation through cache initialization

The authenticated Windows V429 run proved the hardware-initialization
prefix with native MSVC x64 execution. Linux V428 separately verified
the cache initializer and original error-handler registration to the
data-initializer entry. This change reuses that exact Linux patch and
observer contract on the existing Windows build lane. It does not
claim a Windows cache result before the owner job passes.

The Windows workflow now selects `cache` by default. Manual dispatch
also accepts `startup`, `hardware`, `data` and `os-entry`, with the
last two remaining candidates pending original-game verification.
The original-free translated byte-reverse control stays unchanged.
All owner binaries, generated code and private logs remain ephemeral.

Every scope uses its exact ordered witness and patch prerequisites.
Cross-scope markers and unknown witness markers are rejected, including
the V430 success marker embedded in a longer V433 continuation. Nonzero
Windows exception codes cannot wrap to a successful POSIX status.

Local Python regression: four test methods, all 25 scope/source pairs,
35 nonzero exit-code controls, 10 missing/duplicate terminal controls,
25 unexpected marker controls, and log-size/invalid-scope checks pass
against the repository audit functions. MSVC and original-image results
remain separate CI gates.
