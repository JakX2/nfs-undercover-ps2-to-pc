# V436: verified Linux OS entry carried into Windows with a checked DOL loader

The authenticated V433 full-image Linux run 45314252849 reached original
OSInit after DBInit. V434 Windows run 45314820997 verified all 13 hardware
and cache stages, exit zero and no interpreter fallback. V435 original-free
OS-time tests have passed, but its owner execution remains a candidate.

The Windows push default now targets the already Linux-verified OS entry.
Manual dispatch additionally accepts os-time. All six scope contracts
reject foreign or malformed witness markers. Existing scopes are retained.

The native Windows builder now compiles an independent DOL equivalence
control against the actual unmodified upstream loader. The hardened V431
reader validates the image first; entry, ordered section metadata, flags,
every byte of each initialized section, and BSS representation must agree.
A strict reload must also agree. Only after that gate passes and the
original translator generates the complete image is the V431 loader
installed in the generated runtime, before native configuration.
The synthetic translated swap control uses the same path. The explicit
--legacy-loader CLI option and manual workflow boolean preserve the old
runtime loader as an independent control. No game bytes are printed.

Local C++20 ASan/UBSan passed the comparator's equality control and nine
deliberate mismatches. Windows original-free and owner-image CI are the
separate integration gates. The source-only tests also check build order.
Neither a verified full OSInit nor game main or gameplay is claimed.
