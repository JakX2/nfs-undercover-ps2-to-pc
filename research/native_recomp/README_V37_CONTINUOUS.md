# V37 candidate: authentic exception-template clearing in continuous Wii __start

**Status: VERIFIED** by original-game Wii Continuous Startup Checks
[owner-original run 44015047562](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44015047562)
on November 17, 2026. All twelve V26–V37 authentic continuous native
checkpoints passed from Wii `__start` (`0x8000403C`); the final
instrumented test-only stop is `0x80520D80` with `stage=37`.
The earlier directly entered OSInit V41 test is a separate execution lane.

## Scope

V37 continues the SHA-pinned original Wii __start from the latest
verified original OSInit -> OSExceptionInit/mark-helper sequence. It
restores the original PowerPC block 0x80520CC8..0x80520D7C, including
the original mark-result branches and genuine mtctr/bdnz/stw-controlled
template-clearing code. A source-only constructor extracts only exact
original owner PPC bytes into private runner scratch.

The stage targets the original unmarked exception index-zero branch.
The authentic mark helper at 0x804E50A0 returns the unset mask bit from
the real DBInit-initialized Wii debug memory at 0x80000040 and the original
exception routine updates one guest instruction word at 0x80520F18 to
0x60000000. The test seeds independent canaries at 0x80520F14 and
0x80520F1C, asserts the exact one-word update with both neighbors
unchanged, verifies CTR reached zero and original loop ABI state, and
retains all preceding V26–V36 checks for genuine hardware, interrupts,
floating point, OS globals, arena setters and IPC pointer setup.

The final explicit test-only syscall at **0x80520D80** is before original
exception vector-target computation, vector copies, DC flush or IC
invalidate. Neither those cache operations nor exception-vector
installation is claimed. Original debug-print callsites at 0x80520CDC
and 0x80520D08 are replaced by fail-closed synthetic stops for
unimplemented debug-service branches. The original earlier debug path
0x80520C44 and original __OSInitSystemCall 0x805208AC also remain guarded.
All original code except documented test-only stops is byte-verified
against the owner SHA-256-pinned executable.

## CI and reproduction

The source-only geometry test checks the original branch and loop
spans, real mark-helper body, private DOL code/data section bounds,
source-word integrity and every documented stop. An additional 22-case
owner-only negative suite mutates original/guarded PPC words, the helper,
private header geometry and SHA-pinned owner input to prove fail-closed
rejection before native code generation. Native CI must pass
V26–V36 beforehand, then require stage=37, original entry 0x8000403C,
exact observed syscall PC 0x80520D80 and sixteen passing owner-original
native cases. No original game-derived code or raw private native logs
are uploaded or published. Failures expose only public test-stage
labels and numeric assertion codes.

    bash run_v37_continuous_vectorclear.sh /private/NWiiRecomp /private/NfsMWRelease.dol

A passing V37 would still mean partial original Wii OS initialization
only. The original game main(), full Wii OS/IOS, Windows-native game
startup, graphics, frontend and playable racing are not reached.
