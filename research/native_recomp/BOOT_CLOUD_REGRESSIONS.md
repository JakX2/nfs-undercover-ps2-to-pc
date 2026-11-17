# Authenticated cloud native regressions (Undercover Wii)

The repository's cloud Ghidra deployment was merged to main as PR #37,
commit b4f8b5d5bcadf6674d550932dd47080f88ddf37a. The
research/wii-native-recomp-preflight branch adds a separate workflow,
.github/workflows/wii-native-private-boot.yml, for authentic native tests
whenever independently authored native-recomp source changes.

## Automatic behavior

1. Source-only syntax and boot-checkpoint unit tests run on qualifying pushes,
   with no game executable or Google credentials.
2. With `WII_GHIDRA_PRIVATE_ENABLED=true` and the two Actions secrets
   `WII_ORIGINAL_DOL_ID` and `WII_ORIGINAL_ELF_ID`, source-only `gdown`
   staging retrieves owner-provided Wii inputs in a private GitHub runner,
   verifies pinned SHA-256 fingerprints, and fetches original-free
   NWiiRecomp at immutable commit
   `595f176f1d24cc54ff2e8389feed12d7fb553cc2`.
3. The private job recompiles and tests both the independent direct-entry
   `OSInit` V68 regression and the continuous original `__start` lane
   through V51. `boot_progress.py` asserts exact original guest PC/stage
   advancement. Failures withhold raw logs; owner Wii files, derived game
   C++, code shards and private traces are never published or cached.

No duplicate scheduled task is needed. The existing research-branch CI and
hourly owner development task are already enabled.

The V68 direct-`OSInit` runner is a separately verified native regression
ending at `0x804EFA34`. It has **not** been joined to genuine continuous
`__start` execution or a complete boot.

**Latest verified continuous Wii `__start` frontier: V51,
`0x805208C4`.** Original AOT-compiled Wii startup now executes through
full exception-vector and syscall-vector initialization; original alarm
and shutdown registration; module initialization; interrupt table
clear and genuine IRQ hardware register writes; the complete original
seven-bank `SetInterruptMask` loop; native IRQ return to `OSInit`;
`__OSContextInit`; and **the authentic second `__OSCacheInit` call**.
The same SHA-pinned original Wii cache initializer also executes during
the early original `__start` path. Sixteen owner-original native trials
and synthetic startup passed
[CI run 44190097982](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44190097982).
V50 at `0x805208C0`, V49 at `0x805208BC`, V48 at
`0x805266AC`, V47 at `0x80526698` and all preceding stages remain
regression-verified. Some hardware/MMIO and debug services remain
controlled test-only callbacks, **not device implementations**.

Next original continuous service: `OSInit` calls `EXIInit` at
`0x805208C4` (target `0x804EF9BC`). The separately verified
V65/V66/V68 direct-entry EXI tests are evidence for the code path only;
they do not prove continuous `__start` reached it.
Never publish source-owner Wii binaries, game-derived C++ or raw private
logs. No original game `main`, first frame, frontend or gameplay yet.

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
continuous native V51 passed after independent V38–V50 owner-original
baseline checks; the historical direct-entry OSInit V68 lane remains separate.
A successful private CI check is evidence for the exact assertions it ran,
not for full native Windows startup, game `main`, or graphical output.
