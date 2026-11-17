# Boot-first native recompilation loop (source-only tooling)

## Why this exists

As of November 17, 2026, the pinned original Wii executable is verified
through **continuous native V51 at `0x805208C4`**, starting from genuine
`__start` at `0x8000403C`. The path uses NWiiRecomp AOT-generated native
C++ and includes original `OSExceptionInit` (15 vectors plus
`_restgpr_20`), `__OSInitSystemCall` (the authentic 28-byte handler at
`0x80000C00` and 83 cache lines), `__OSInitAlarm`/shutdown list,
`__OSModuleInit`, `__OSInterruptInit`, original seven-bank
`SetInterruptMask`, the complete interrupt return into `OSInit`,
`__OSContextInit`, and a **second native call to the same original
`__OSCacheInit`** function earlier invoked during `__start`.

V51 verifies both original cache callsites and the second guest return LR
`0x805208C4`, preserving the OSInit stack ABI. The SHA-verified
owner-original 16-trial native tests and independent synthetic tests passed
[GitHub Actions run 44190097982](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44190097982).
Earlier V50 `0x805208C0` was verified in
[run 44185965547](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44185965547);
V49 returned from interrupt initialization at `0x805208BC`; V48
completed its seven-bank mask loop at `0x805266AC`; V47 executed the
IRQ-disable/mask preparation at `0x80526698`.
These are bounded native original-code execution milestones, **not** a
complete game boot. Guest PCs need not increase monotonically across calls.

**Remaining emulation boundary:** the interrupt-controller MMIO callbacks
provide deterministic test-only read/write values and traces, not a working
PI/IOS hardware device. Debug printing and selected OS services are still
test-only callbacks. Original game binaries and generated translated game
C++ are kept in private ephemeral CI directories.

The separately verified V68 **direct-entry** `OSInit` regression reaches
EXI initialization at `0x804EFA34`. It is not continuous original
`__start` execution. Neither lane has reached original game `main`,
a rendered frame, the frontend, or playable gameplay.

**Next blocker:** the original `OSInit` call at `0x805208C4` reaches
`EXIInit` at `0x804EF9BC`. Reuse the exact owner-original direct-entry
V65/V66/V68 EXI polling/call-graph guards while adding a bounded V52
continuous-start test. Implement missing EXI/PI/IOS device semantics only
as required, and do not conflate controlled hardware callbacks with real
device emulation.

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
