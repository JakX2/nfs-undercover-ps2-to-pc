# Authenticated cloud native regressions (Undercover Wii)

The repository's cloud Ghidra deployment was merged to main as PR #37,
commit b4f8b5d5bcadf6674d550932dd47080f88ddf37a. The
research/wii-native-recomp-preflight branch adds a separate workflow,
.github/workflows/wii-native-private-boot.yml, for authentic native tests
whenever independently authored native-recomp source changes.

## Automatic behavior

1. Source-only syntax and boot-checkpoint unit tests run on qualifying pushes,
   with no game executable or Google credentials.
2. Once WII_GHIDRA_PRIVATE_ENABLED=true and the three existing cloud Ghidra
   secrets are configured, the private job authenticates to the Drive API,
   verifies SHA-256-pinned NfsMWRelease.dol and NfsMWRelease.elf, and obtains
   original-free NWiiRecomp at immutable Git SHA
   595f176f1d24cc54ff2e8389feed12d7fb553cc2.
3. It recompiles and runs the original V68 OSInit native tests using the
   source-only boot_progress.py wrapper. Failures withhold private logs, and
   original executable bytes, generated game C++, temporary files and traces
   are not uploaded or cached.

The private job is deliberately **skipped** until the existing Ghidra secrets
and feature variable are set. No new scheduled automation is created; this is
continuous integration triggered by research-branch code updates.

The V68 direct OSInit runner currently emits PASS: lines but does not emit
verified BOOT_PROGRESS markers. A passing run therefore gets
passed_uninstrumented, not proof of continuous __start advancement. The next
genuine development step is recovering the unpublished V26 startup harness,
removing its test-only terminal at 0x805206B4, and connecting V68's authentic
OSInit startup continuation to the original __start call.

## Verified owner-ELF native-boot frontier

The owner ELF32 PowerPC file is not stripped. A private symbol/direct-BL
analysis (not Ghidra and not native execution) identified 27,941 named
functions and 87,626 statically resolved BL call sites. At 0x805206B4 the
real program calls __RAS_OSDisableInterrupts_begin (0x805265AC), a helper
already translated in V26, but the V26 test harness replaced the callsite with
a synthetic stop. The next OSInit original call at 0x805206BC reaches
__OSGetExecParams (0x80523B1C), and the performance-register helpers follow.
The V68 direct-OSInit lane reaches 0x804EFA34 separately.

These results are exact private-owner function/disassembly observations, not
a new native boot milestone. Keep PR #36 draft and original game-derived
translations/private symbol manifests off GitHub.

## Simplified link-based Drive setup (2026-11-16)

Merged PR #38 deployed the original-safe gdown staging script to main commit
59e8af244d1e8105a04029ec35b95baf34fc5084. Native CI checks out this
pinned source-only revision. The two original Wii files are already Drive
link-readable. Owners now configure only WII_ORIGINAL_DOL_ID and
WII_ORIGINAL_ELF_ID under repository Actions Secrets, and set repository
Actions Variable WII_GHIDRA_PRIVATE_ENABLED=true. No Google Cloud service
account is needed. Link sharing is not authentication: anyone with a known
Drive link can retrieve the file. All downloads are SHA-256 pinned and
checked privately; owner binaries and game-derived C++ are never uploaded.

The original V68 native regression will remain skipped until the variable is
enabled. Its first true owner-original CI result remains unverified.
