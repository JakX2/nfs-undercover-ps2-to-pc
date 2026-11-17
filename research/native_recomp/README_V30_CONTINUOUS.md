# V30 continuous original Wii __start: HID4, speculation and FP-mode seam

Status: VERIFIED in authentic owner-original GitHub Actions run
44004274082 (November 17, 2026). The runner passed its original continuous
V26/V27/V28/V29 baselines and native V30 original HID4/speculation/non-IEEE FP
continuation, recording an advanced instrumented guest-PC stop 0x80520700,
stage=30. This is a bounded test, not full OSInit or a playable Windows game.
A separately entered older direct-entry V30 regression remains independent.

## Original execution under test

- Entry is authentic original Wii __start 0x8000403C. Exact V26/V27/V28/V29
  native checkpoints must first pass in the same isolated runner.
- Original OSInit PowerPC instructions 0x805206F0..0x805206FC replace the V29
  test-only SC/BLR at 0x805206F0.
- Three original BLs target PPCMthid4 0x804B7A30,
  PPCDisableSpeculation 0x804B7A00 and PPCSetFpNonIEEEMode 0x804B7A28.
- Nested original PPCMfhid0 (0x804B7920) and PPCMthid0 (0x804B7928)
  execute within the real speculation-disable routine.
- PPCMthid4 writes guest HID4 value 0x83900000. PPCDisableSpeculation
  preserves other HID0 bits and sets 0x200. PPCSetFpNonIEEEMode sets the
  original guest FPSCR bit 0x4 (PowerPC bit number 29).
- All code is extracted solely from the owner's SHA-256-pinned original DOL
  into temporary files; NWiiRecomp-generated C++ stays in the runner.
- Original HID4 bit-31-clear branch to OSReport 0x80522F00 is guarded by an
  explicit synthetic syscall. The normal original OSInit sets bit 31; do not
  claim original OSReport or its return behavior was implemented.
- Exact new test-only callback stop is 0x80520700. Native C++ asserts actual
  dispatch and full carried-forward startup/register/MMU/FPU/BSS contracts
  over sixteen owner-original cases.

## Original-free runtime patch compatibility

The older direct-entry apply_hid4_fp_v30.py assumes HID0 is unimplemented
at patch time, but the recovered continuous path already uses native
HID0/HID2 from V18, Wii L2CR from V20, performance SPRs from V29, and
exact syscall PC from V26.

apply_hid4_continuous_v30.py is a separate strict, idempotent atomic patch
for *that already installed* runtime state. It only adds HID4 value emission,
mtfsb1/mtfsb0 FPSCR bits, and HID0/HID4 backup state. It does not duplicate
the existing original-free HID0 model or implement physical Wii speculative
execution, caches, performance-counter events or FP exceptions.

test_hid4_continuous_patch_v30.py verifies safe idempotence, atomic refusal
of unknown or partial source layouts and the harmless-comment case with
independent synthetic strings. The gated owner CI patch step refuses
incompatible runtime and does not publish source or game artifacts.

## Reproducibility and limits

In a fresh isolated NWiiRecomp checkout first run the V29 continuous owner
runner, which installs and validates the V29/HID/L2 upstream patches, then:

    bash run_v30_continuous_hid4.sh /private/NWiiRecomp /private/NfsMWRelease.dol

The GitHub Actions owner job checks a V29 instrumented baseline, then runs
the V30 generated native entry with --require-progress and expected PC
0x80520700. Only a verified original-code 16-trial native pass may emit
BOOT_PROGRESS stage=30. All original game code, private analysis and raw
logs remain ephemeral; no artifacts uploaded.

No complete OSInit, game main, frontend, graphics frame or playable
Windows build is implied by a successful bounded V30.
