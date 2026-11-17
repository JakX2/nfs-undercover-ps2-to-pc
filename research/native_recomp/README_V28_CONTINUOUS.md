# V28: continuous __start through authentic __OSGetExecParams (candidate)

Status: owner-original CI validation pending. Do not treat this source-only
test harness as a new verified native boot checkpoint until the gated
original-code GitHub Actions job succeeds.

Existing V27 passed from authentic original Wii entry 0x8000403C through
the original system-time and post-time interrupt-disable instructions,
stopping at a deliberately inserted syscall at 0x805206BC.

This new independent source-only V28 fixture reuses exact original V27
test DOL geometry. It replaces the synthetic sc/blr at the original
OSInit BL callsite 0x805206BC with the actual original PPC BL targeting
__OSGetExecParams at guest 0x80523B1C, inserts the complete authentic
36-byte helper function (private user DOL source only), and changes
the next synthetic stop to 0x805206C0, before later performance-register
and OS/IOS calls. It keeps source and generated C++ in temporary private
runner storage and deletes them at job end.

The code generator and native test preserve the previous V26/V27 verified
startup memory, register, timebase, MSR/cache/paired-single and genuine
call-path assertions. The new checks require entry of __OSGetExecParams
with authentic return LR 0x805206C0 and exact native guest-PC syscall
callback. The owner runner emits the explicit stage-28 BOOT_PROGRESS marker
ONLY after all sixteen complete original-code native trials and the
expected anchored PASS line have succeeded.

The GitHub workflow compares V28 against an instrumented and separately
verified original V27 baseline using --require-progress and exact
--expected-entry 0x8000403C and --expected-pc 0x805206C0. No equality
between directly entered OSInit V68 and continuous entry is inferred.

Reproduction privately on a pinned NWiiRecomp checkout:
    bash run_v28_continuous_execparams.sh /private/NWiiRecomp /private/NfsMWRelease.dol

No complete Wii OSInit, original main(), frontend, rendering or gameplay
is claimed. This is a test harness for another bounded native execution
step, not the complete native Windows game.
