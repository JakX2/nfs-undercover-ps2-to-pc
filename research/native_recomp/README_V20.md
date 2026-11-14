# V20: Original Undercover Wii `__OSCacheInit` executes natively with bounded L2CR state

**Verified isolated native execution, NOT a bootable Undercover PC port.**

The owner's original `NfsMWRelease.dol.bin` (SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`)
provides a complete 312-byte, 78-instruction `__OSCacheInit` at
`0x80522540`. V20 translates that **original PPC body** and original cache/MSR
register helpers using the upstream NWiiRecomp analyzer and C++20 generator.
The generated code executes on the host through NWiiRecomp's **real
`run_game(nwii::runtime::CPUContext&)` dispatcher**. There is no PPC interpreter
fallback in the tested paths.

The private test-DOL also contains the previously verified `__start` prefix at
`0x8000403C`, `__init_registers`, `__init_hardware`, `__OSPSInit`,
`__OSFPRInit`, and the original HID/GQR/cache helper functions. A separate,
entirely independent synthetic DOL uses hand-authored PowerPC instructions and
tests the same generated dispatcher and guest CPU state.

## Actual Wii cache dependencies

The original `__OSCacheInit` function contains **26 direct calls, 5 conditional
branches, and 6 sync instructions**, validated against the owner's DOL. Its
original callees used in this test are `PPCMfhid0` at `0x804B7920`,
`PPCMfmsr` at `0x804B7910`, `PPCMtmsr` at `0x804B7918`, `PPCMfl2cr`
at `0x804B7930`, and `PPCMtl2cr` at `0x804B7938`. These helper bodies are
**not stubs** in owner mode. The recompiler discovers exactly **18 functions**
in each synthetic/private test image.

Four genuine external service bodies have **not** been implemented: `ICEnable`
(`0x805223BC`), `DCEnable` (`0x80522280`), `DBPrintf` (`0x804E50B8`), and
`OSSetErrorHandler` (`0x805230B8`). Their entry points contain **test-only
`sc; blr` callbacks** so the original `__OSCacheInit` can continue and the
call order and arguments can be inspected. The first two are exercised when
L1 caches are initially disabled. `OSSetErrorHandler` verifies exception
index 1. The entire function returns into a test-only stop just after the
second original `__start` branch. `__init_data`, `OSInit`, and the game's
`main` are **not entered**.

## Guest L2 cache-control state

`apply_l2cr_v20.py` adds bounded, fail-closed support for Broadway's
L2CR (SPR 1017) to **original-free runtime code**:

- `mfspr` reads guest `CPUContext::read_l2cr()` instead of a hardcoded zero.
- `mtspr` calls `CPUContext::write_l2cr()` rather than silently ignoring writes.
- `L2E = 0x80000000` reflects software-visible cache enablement.
- `L2I = 0x00200000` is a software-managed global invalidate command.
- `L2IP = 0x00000001` is read-only. Writing bit 0 cannot manufacture busy status.
- An L2 invalidate request with the L2 cache disabled produces **two busy
  polls** before `L2IP` clears. This deterministic finite handshake allows
  original Wii polling code to advance without an infinite loop.
- The original PowerPC code clears `L2I` itself and eventually sets `L2E`.
  Other modeled register bits are preserved unless original game instructions
  explicitly change them.

**Hardware limit:** The busy duration is synthetic and not cycle-accurate.
This does **not** simulate cache lines, cache coherency, L2 invalidation
side effects, the real HID0 ICFI self-clearing command, physical instruction/
data-cache enabling, or error-handler registration. It is a validated native
startup control-flow bridge, not complete Wii hardware emulation. Even the
original CacheInit function's apparent completion must not be equated with
full runtime readiness.

## Reproduce

Use an isolated NWiiRecomp source checkout. Python 3 and a C++20 compiler
(GCC tested) are required. The script applies the preceding original-free V15,
V18, V19 patches and the new V20 patch to that local checkout. It refuses
conflicts, is idempotent on repeat runs, and writes proprietary output only to
`mktemp -d` (removed on exit).

```bash
bash run_v20_tests.sh /private/path/NWiiRecomp-master
bash run_v20_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V20_SANITIZE=1 bash run_v20_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

Do not commit or distribute the temporary sliced DOL or generated `output.cpp`.
The public files include only independently written C++/Python tests, patches,
PowerPC synthetic fixtures, and documentation.

## Verified results

| Test | Result |
| --- | ---: |
| Original Wii native cache dispatch, 128 startup trials | **12,290 assertions passed** |
| Independently authored synthetic native cache dispatch, 128 trials | **12,034 assertions passed** |
| Independent L2CR state/handshake test | **3,584 assertions passed** |
| Invalid inputs, output safety, patch conflict/idempotence (owner mode) | **21 checks passed** |
| Original Wii L2CR guest reads/writes | **704 reads / 320 writes** |
| Original Wii substitute OS service calls | **704 explicitly identified test callbacks** |
| Entire normal test runner | **Passed** |
| Entire ASan+UBSan test runner | **Passed** |
| Fresh upstream NWiiRecomp checkout, synthetic-only runner | **Passed (20 safety checks)** |

Native original-game runs exercised all eight combinations of initially
on/off L1 instruction cache, L1 data cache, and L2 cache. L2-off cases run
through the original software invalidation/polling loops. All 128 original
startup slices returned to the original post-hardware instruction boundary
without interpreter fallback or unexpected synthetic syscalls.

## Next work

Implement the original `ICEnable` and `DCEnable` service functions and their
actual guest-visible HID0 behavior. Audit and model `OSSetErrorHandler` and
its OS global state, then progress beyond the bounded post-hardware stop into
original `__init_data` and subsequent Wii OS initialization. Need to validate
cache-command self-clear semantics and memory ordering against authentic Wii
behavior, and later link the full translated executable. **No genuine native
boot, frame, frontend or gameplay has been demonstrated.**
