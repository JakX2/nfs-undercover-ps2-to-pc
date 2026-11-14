# V25: Undercover Wii `OSInit` authentic prologue now executes natively

**Status:** Verified bounded native execution through original `OSInit` prologue; **not** full Wii OS initialization or a game boot.

This source-only toolkit extends the original-game `__start` -> hardware setup ->
`__init_data` -> `DBInit` path established in V24. The real `__start` call at
`0x8000415C` now transfers into the **first 60 bytes (15 PowerPC instructions)**
of the original `OSInit` at **`0x80520670`**. This prefix creates the real 80-byte
OSInit stack frame, saves the caller's link register, calls the **complete
52-byte original `_savegpr_20`** at **`0x805450E8`**, checks the one-time OS-init
global at **`0x8070DAFC`**, writes the value **1** to this global, and makes its
original `bl` to **`__OSGetSystemTime` at `0x8052A844`**.

`__OSGetSystemTime` has an **explicit synthetic `sc; blr` stop**; that function's
real body does not run. Only the OSInit prologue before the call runs. The
previous V24 synthetic `OSInit` entry stop is removed, but prior `DBPrintf`
and `OSSetErrorHandler` test-only boundaries remain. The original unexecuted
"already initialized" branch target at `0x80520BDC` is also an explicit
synthetic stop rather than a fabricated implementation. The remaining original
1,412-byte `OSInit` function is **not** recompiled or executed by this test.

## Native test scope and observations

* The owner-supplied `NfsMWRelease.dol.bin` must match SHA-256
  `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
  All original executable bytes are extracted **only locally and privately**.
* The actual NWiiRecomp analyzer discovers **28 function entries** in the owner
  image, including original `OSInit` and `_savegpr_20`, and **23 entries** in an
  independently authored synthetic DOL. Both are translated by NWiiRecomp's
  non-split `run_game(CPUContext&)` generator. There is no PPC interpreter
  fallback in the tested path.
* The helper saves `r20`–`r31` at the expected 12 stack locations. In this
  particular original startup path, the saved `r31` is **`0x80004044`**,
  inherited from prior original hardware initialization. The other saved
  nonvolatile registers are zero. The original `OSInit` then loads
  `r30=0x806F4F00` and `r31=0x8060B7A8` before the time call.
* The OSInit one-time flag is written as a big-endian guest word within the
  original BSS range already verified in V22–V24. Its four bytes, along with
  the eight DBInit global bytes, are excluded from the final all-BSS-zero
  assertion; all other **963,444 bytes per trial** remain zero, with canaries.
* The synthetic fixture uses a **96-byte** OSInit stack frame, an independent
  PowerPC register-save helper and a guest-memory marker, allowing the same
  emulator-independent native dispatch and call-stack assertions to detect
  assumptions tied to the original function's incidental instruction choices.
* To respect DOL's **seven text-section limit**, the private bounded test image
  extends one test-only NOP-filled text section to include the original
  `_savegpr_20` at its real address and the synthetic time-service stop. This is
  test fixture layout only, **not a claim about the real game's code layout**.

## Reproduction

From this folder, with a separate upstream NWiiRecomp checkout, Python 3,
C++20 GCC, and optionally the owner-provided DOL:

```bash
bash run_v25_tests.sh /private/NWiiRecomp-master
bash run_v25_tests.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V25_SANITIZE=1 bash run_v25_tests.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner idempotently applies the existing V15 non-split emitter fix and
V18/V19/V20 original-free HID0/HID2, FPSCR, L2CR runtime patches. It creates
private derived DOL and generated game C++ only inside an automatically
removed temporary directory. The compiler retains V24's narrowly scoped
`-Wno-type-limits` workaround for generated unsigned comparisons to zero;
other warnings remain fatal. The kit does **not** contain or write any original
game source, assets, binaries, or generated game-derived C++ to GitHub.

## Verified local tests

| Test | Result |
| --- | ---: |
| Original Undercover full bounded startup, 16 runs | **15,417,532 assertions passed** |
| Independently authored synthetic PowerPC startup, 16 runs | **2,008 assertions passed** |
| Original/Synthetic native translated function entries | **28 / 23** |
| Invalid DOL, function alteration, owner SHA mismatch, output overwrite checks | **48 passed** |
| Release-mode native dispatcher and runtime | **Passed** |
| AddressSanitizer and UndefinedBehaviorSanitizer owner and synthetic paths | **Passed** |
| Fresh, unmodified NWiiRecomp archive (synthetic-only test) | **Passed, including 38 safety checks** |

The source tests verify the original stack frame, guest GPR saves, OS init flag,
original and synthetic BL target / return addresses, all earlier original
startup hardware and data work, original BSS results, and zero interpreter
fallback. A failed assumption about `_savegpr_20`'s saved `r31` was corrected by
observing the original hardware caller's preserved guest state, **not** by
editing translated game code. No new functional blocker was found.

## Remaining dependencies

`__OSGetSystemTime` is the next unresolved original Wii service. Its timebase,
calendar/state semantics and 64-bit return (`r3:r4`) must be verified before
continuing the rest of `OSInit`. The later calls to interrupt services, memory
management, low-level IOS, DVD, graphics, audio and frontend code have not been
executed. `OSSetErrorHandler`, `DBPrintf`, cache coherency and detailed hardware
timing remain incomplete or explicit test placeholders. This work does **not**
establish full native startup, original game `main`, a rendered frame, frontend,
or playable Windows gameplay.
