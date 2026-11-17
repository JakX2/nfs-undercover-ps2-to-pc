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

The V68 direct-`OSInit` runner is a separately verified native regression.
Its direct-entry progression does not establish continuous `__start`
execution or a complete boot. The earlier V26 startup harness has since
been recovered and extended through V41. The current continuous frontier
is **`0x805208AC` after the original `OSExceptionInit` return**, verified
with the authentic register-restore thunk, final exception table and all
15 vector handlers in
[workflow run 44029703720](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44029703720).
Earlier V40 at `0x80520E58` and V39 at `0x80520DB8` remain passing
independent regressions. The V41 `DBPrintf` callback is test-only.
Maintain the two checkpoint lanes separately.

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

The private-original workflow has since run successfully with the feature
variable enabled, using SHA-pinned owner inputs. On November 17, 2026
continuous native V41 passed after independent V38, V39 and V40 baseline checks.
A successful private CI check is evidence for the exact assertions it ran,
not for full native Windows startup, game `main`, or graphical output.
