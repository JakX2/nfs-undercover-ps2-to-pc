# V289–V293 correction: authentic NAND child was NOP-reduced in native test fixture

**Date:** 2026-11-22. **Branch:** `research/wii-native-recomp-preflight`.

## Milestone nomenclature correction

The original Nintendo Wii PowerPC entry `0x8052FA60` was reached and
returned in the authenticated owner-native tests. **That does not mean
its original function body executed in those tests.**

Owner-private [V292 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44977573034)
compared the SHA-256-authenticated Wii DOL against the *actual
reduced DOL fixture* used for the restored NAND callback and the
NWiiRecomp-generated C++ linked into the native executable.
It established:

```text
V292_AOT_REACH owner=1 fixture=1 targets=4 child_original=0 source_original=0 child_aot=1 source_aot=0 child_bl=0 unmapped_bl=0 direct_emit=0
V292_AOT_TARGET pc=8052fa60 words=48 present=1 same=0 nop=48 blr=0 other=0 emitted=1 dispatch=1
V292_AOT_TARGET pc=8051d20c words=30 present=1 same=0 nop=30 blr=0 other=0 emitted=0 dispatch=0
V292_AOT_TARGET pc=8051e150 words=34 present=1 same=0 nop=34 blr=0 other=0 emitted=0 dispatch=0
V292_AOT_TARGET pc=8052fca4 words=16 present=1 same=0 nop=16 blr=0 other=0 emitted=0 dispatch=0
```

All audited words in these four spans were **NOP placeholders**.
The child had a translated function and dispatch entry but not the
original instructions. The other three were not emitted as original
AOT functions at all. The original callback at `0x8051E06C`
*was* restored separately in V247/V248 and did genuinely execute.
Do not confuse the authentic parent callback with the reduced child.

This explains why the V278/V281/V285 native entry censuses saw zero
calls into the original status writer or its guarded service functions:
those instructions were not in the compiled AOT fixture.

## Branch evidence and corrected live input

Earlier owner-original ELF static audits identified a `cmpwi r3,0`
at NAND child `+0x08`, followed by a `bne` at `+0x18`
that would skip to `+0x5C` if the input were nonzero.
At `+0x50` there is an original linked call to `0x8051D20C`.

The **first V289 native test was invalid** because its observer
classified `ctx.lr==0x8052FAB4` instead of the incoming `r3`.
An initial aggregate looked like 16 nonzero inputs; it was a
*link-register observation*, not a GPR3 observation.

[Corrected V289 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44976542643)
changed that observer to `ctx.gpr[3]==0` and passed both jobs:

```text
V289_NAND_ENTRY trials=16 frontier=64 stable=1 distinct=1 entries=16 min_trial=1 max_trial=1 pre=16 post=0 zero=16 sc1=16 sc3=0
```

All 16 sampled NAND-child entries had **r3 = 0**, making the
original first `bne` condition **false**, not true.

[Corrected V290 CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44976816979)
independently proved that the *original ELF's* first two PPC
instructions preserve r3. [V291 owner CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44977026269)
proved the original CR0 comparison state is preserved between +0x08
and +0x18, and there are zero original control transfers between
+0x1C and +0x4C:

```text
V291_NAND_FALLTHROUGH child=8052fa60 cmp=8 branch=24 service_call=80 cr0=preserved between_keep=3 between_write=0 between_unknown=0 between_control=0 events=0 conditional=0 direct_call=0 direct_jump=0 lr=0 ctr=0 system=0
```

The prior missing native callee is **not evidence of a translator
branch bug**. The full original code was absent from the test fixture.

## V293: private restoration feasibility verified

[Original-owner V293 validation](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44977971369)
recovered exact function lengths from SHA-pinned Wii ELF symbol records
and restored only NOP-only private DOL spans from the SHA-pinned
owner Wii DOL. No game-derived code or instruction words were
committed or uploaded.

```text
V293_NAND_RESTORE owner=1 funcs=4 changed=195 total_words=195 roundtrip=1 candidate=1
V293_RESTORED pc=8052fa60 words=52 already=0 nop=52 foreign=0
V293_RESTORED pc=8051d20c words=30 already=0 nop=30 foreign=0
V293_RESTORED pc=8051e150 words=34 already=0 nop=34 foreign=0
V293_RESTORED pc=8052fca4 words=79 already=0 nop=79 foreign=0
```

Restoration is **byte-for-byte reversible**. Every target's original
word was authenticated, and none of the prior fixture words were
foreign instructions. V293 deliberately did **not** execute the
restored code. The candidate remains owner-private in the CI scratch
directory and is deleted by the job cleanup.

## Next gates, without boot claims

V294 separately regenerates a native candidate from the
four restored original functions and requires all four AOT bodies,
dispatch entries, and the authentic linked call to the first NAND
service. It then compiles and links that candidate but **does not
execute unverified restored code**.

If V294 links, follow with a *new* bounded native trial that reaches
the first original instruction or original service-entry checkpoint.
Any missing instruction support or unmapped dependency must be
implemented against the original, not bypassed by altering guest r3,
branch conditions, NAND completion data, IOS replies or SYSCONF.

V292/V293 are **AOT fixture and restoration milestones**, not
confirmation of original game `main`, complete boot, graphics,
frontend, race selection, or gameplay. The standing hourly development
task already exists; do not create a duplicate.
