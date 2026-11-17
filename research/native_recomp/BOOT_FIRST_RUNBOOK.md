# Boot-first native recompilation loop (source-only tooling)

## Why this exists

As of November 17, 2026, original Wii `__start` now reaches the
**continuous native V47 checkpoint at `0x80526698`**, inside the authentic
`__OSInterruptInit` function. The pinned owner-original path has traversed
`OSExceptionInit` (including its 15 exception vectors and original
`_restgpr_20` return), `__OSInitSystemCall` (28 owner code bytes installed
at `0x80000C00`), `__OSInitAlarm` and shutdown registration,
`__OSModuleInit`, then the original interrupt initializer with nested
`memset` and `__fill_mem` calls. Genuine PowerPC stores clear the
128-byte IRQ table at `0x80003040`, write the first interrupt-mask words
at `0x800000C4` and `0x800000C8`, then issue two interrupt-controller
MMIO transactions at `0x0C003004` and `0x0D000034`.
The owner-native test checks the respective values `0xF0` and
`0x40000000`, their order, nested stack and memory canaries.
The V47 original PowerPC continuation then calls the real
`__RAS_OSDisableInterrupts_begin` helper at `0x805265AC`, returning
through native ABI at `0x80526678`, and calculates the IRQ mask
`0xFFFFFFF0` stored in guest low memory at `0x800000C4`.
Sixteen owner-original trials passed the full prior native boot graph,
with independent synthetic CI in
[GitHub Actions run 44173650263](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44173650263).

**The MMIO test uses a bounded host callback that only records and verifies
writes; no functional PI/IOS interrupt-controller device is implemented or
claimed.** `DBPrintf` remains a test-only callback. Separate earlier
continuous native milestones are V46 `0x80526674`, verified in
[run 44172509667](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44172509667),
V45 `0x8052664C`, verified in
[run 44170476226](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44170476226),
V44 `0x805208B8` in
[run 44043846082](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44043846082),
V43 `0x805208B4`, V42 `0x805208B0`, V41 `0x805208AC`,
and V40 `0x80520E58`. They remain separate original-game regression steps.
Guest PCs are not monotonic across called functions: **stage order** measures
verified progress.

The separately tested V68 **direct-entry** `OSInit` path reaches EXI
initialization at `0x804EFA34`, but has **not** been joined to continuous
`__start`. Native execution has **not** reached game `main`, full boot,
a rendered frame, frontend, or playable gameplay.

Next, replace the test-only stop at `0x80526698` with authentic original
IRQ mask-loop preparation, including the BL at `0x805266A0` into
`SetInterruptMask` at `0x805266E0`, and verify the first original loop
and bounded IRQ continuation. Independent direct-entry V54/V56 tests
establish the owner-original PPC call graph but cannot substitute for
continuous startup. Keep exact SHA-verified owner
instructions, original-free public tests, no private game code in logs,
and isolated synthetic callbacks only for services not yet implemented.

## Source-only checkpoint and regression driver

`boot_progress.py` is a local command wrapper. It can execute an existing
owner-private build/test runner while writing an atomic, minimal JSON result.
It records the command's return code, pass-marker count, elapsed time,
optional observed guest entry/PC/stage, and an output checksum on failure. It
**does not** store the command, paths, raw stdout/stderr, source DOL, or game-
derived generated C++ in its result.

To test an existing original-code runner **without fabricating a checkpoint**:

```sh
python3 research/native_recomp/boot_progress.py \
  --lane osinit-direct --report /private/boot-results/current.json \
  --timeout 600 --dol /private/owner.dol.bin \
  --sha256 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 \
  -- bash research/native_recomp/run_osinit_eximask_v68.sh /private/NWiiRecomp-master /private/owner.dol.bin
```

Failed runners cannot publish verified `observed_pc` or `stage` fields even if
an early marker appeared before a failure or timeout. The driver rejects report
paths that alias a pinned input or baseline, validates baseline schema and lane,
and prohibits comparison across different pinned owner-image hashes.

A successful legacy test with no instrumentation receives status
`passed_uninstrumented`, **not** a proven new PC. Add this exact marker to a
native test *only after it checked the actual final `ctx.pc` and entry*:

```
PASS: native original __start assertions
BOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26
```

The `stage` is an **explicit, monotonic, test-defined execution checkpoint**,
not the release version or a numeric sort of guest addresses. Reentrant or
higher-address branches can make raw PC comparison misleading. For a later
validated run, supply `--baseline` and `--require-progress` to reject any
unchanged/regressed stage or stop PC. Never compare the `osinit-direct` and
`continuous-start` lanes.

Synthetic source-only driver tests:

```sh
python3 -m unittest discover -s research/native_recomp -p test_boot_progress.py -v
```

## CI and privacy limits

`.github/workflows/native-recomp-source-checks.yml` runs standard-library
checkpoint-driver unit tests, Python syntax checks and shell syntax checks,
without owner game assets. It **cannot** execute the proprietary original DOL,
prove a new boot checkpoint, or substitute for native ASan/UBSan tests.

Do not upload runtime logs, private DOL/ELF, game assets, recompiled game-code
output or private fixture slices to CI. Only independently written source and
safe test-result summaries may enter GitHub. Always inspect the exact
branch/PR SHA before committing, and use regression checks before extending
how far original `__start` executes.
