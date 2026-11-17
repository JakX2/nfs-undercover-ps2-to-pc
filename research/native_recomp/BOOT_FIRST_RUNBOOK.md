# Boot-first native recompilation loop (source-only tooling)

## Why this exists

As of November 17, 2026, original Wii `__start` has been verified through
**continuous-stage V39 at guest PC `0x80520DB8`**, including the authentic
`DCFlushRangeNoSync` and `ICInvalidateRange` cache helpers, their bounded
line traces, memory preservation and sync/isync behavior. The native stage
passed in [GitHub Actions run 44025883648](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44025883648).
The earlier V38 continuous native checkpoint was at `0x80520DA4`.

The separately tested V68 direct-entry `OSInit` path reaches EXI
initialization (ending at `0x804EFA34`), **but has not been joined to
continuous `__start`**. These tests still do not establish game `main`, a
frame on screen, genuine Wii hardware services, or playable gameplay.

Next, extend the original continuous exception-initialization control flow
beyond `0x80520DB8`, reusing the verified direct-`OSInit` modules and
measuring subsequent native entry/stop PCs. Preserve a separate, deliberate
full historical regression run while using the fast current-frontier test
on ordinary pushes. Translating more isolated functions is not itself boot
progress.

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
