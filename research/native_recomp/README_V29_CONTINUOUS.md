# V29 continuous original Wii startup: six performance SPR helpers

Status: VERIFIED in GitHub Actions owner-original run 44003391154
(November 17, 2026). Continuous __start passed V26, V27, V28 and V29,
reaching the instrumented guest-PC test boundary 0x805206F0.
All original PowerPC instruction bytes were read privately from the
SHA-256-pinned owner DOL, never committed or uploaded. The shared
NWiiRecomp checkout must apply the original-free V29 performance-register
patch before V18/V20 modify overlapping mfspr/mtspr source branches.
The runner now checks the resulting combined HID/L2/performance source
without reapplying the pre-HID V29 patch.

The verified continuous path is V26 then V27 then V28 from original
__start (0x8000403C) through original OS time, interrupt disable,
__OSGetExecParams and the test-only V28 stop 0x805206C0.

V29 replaces that test-only stop with all 48 bytes of authentic original
OSInit setup at 0x805206C0..0x805206EC. The code makes six original BL
calls to private original 8-byte PPC helpers at 0x804B7964..0x804B7993.
The six original helper functions each execute an mtspr r3 and blr, with
the authentic register targets: MMCR0 (952), MMCR1 (956), PMC1-4
(953,954,957,958). They are extracted solely from the verified owner
DOL. The existing source-only performance-register patch gives the
native CPUContext observable mmcr0, mmcr1 and pmc value state; it does
not implement physical performance counting, hardware events or MMCR
timing. Native C++ test seeds each register nonzero, checks all six
real PPC writes clear them, and verifies each authentic BL/return
address plus original time, FPU, BSS/cache, exception and startup
contracts inherited from V26 through V28.

A new deliberate test-only sc/blr boundary is placed at 0x805206F0.
The next authentic hardware/performance service call after F0 is
not executed. To pass the owner-original CI, test runner must verify
16 genuine owner test trials with exact stop 0x805206F0 before
emitting BOOT_PROGRESS stage=29; boot_progress.py then requires
stage29 to advance over a separately verified V28 stage28 report.

Repeat privately on the SHA-pinned original and pinned NWiiRecomp:
    bash run_v29_continuous_perfsprs.sh /private/NWiiRecomp /private/NfsMWRelease.dol

The code, original derived output, private symbol map and raw logs
are kept only in ephemeral runner scratch. No source/game originals
are published, and this is not full OSInit, game main, a rendered
frame or gameplay.
