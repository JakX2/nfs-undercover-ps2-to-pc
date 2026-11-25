# V705: generated native EE-disabled mtmsr/timebase leaf control

Independently authored PPC fixture executes three direct calls (two unchanged-EE mtmsr leaves and a timebase leaf), preserving ABI and exception registers. It uses pinned NWiiRecomp, complete native label/edge audit, production V704 witness, split/non-split compilation, ASan/UBSan, and refuses nonvolatile corruption. No actual callback is expected during disabled mtmsr. CI pending; original post-ACK route still unchanged.
