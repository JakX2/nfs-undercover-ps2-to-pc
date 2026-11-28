# Windows owner-original Wii startup frontier, November 28, 2026

Branch: research/wii-native-recomp-preflight, draft PR #36. This ledger
records authenticated **complete-image Windows x64 original AOT execution**
separately from Linux isolated-owner fixtures and original-free Windows
tests. Static source analysis, an installed observer and a successful
compiler/link do not prove execution through a new original call.

## Verified continuous Windows original code

| Boundary | Authenticated original-owner Windows result | What executed |
| --- | --- | --- |
| Post-time, pre-fourth SI | [46095473544](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46095473544) | Original third system-time helper return; stop before fourth handler call |
| Fourth SI entry and pre-MMIO save/disable | [46096246382](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46096246382), independently rerun [46098038611](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46098038611) | Original __SITransfer entered; compiler GPR save and interrupt disable reached |
| Fourth SI native device and ABI return | [46098038611 owner-return](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46098038611), plus independent full callback [46099124041](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46099124041) | V777 original_return=1, irq_restore=1, compiler_restore=1, idle=1, SI reads=2 writes=3, follow=3 and pending=0. Handler return remains 0 |
| Fifth alarm-cancellation return | [46099124041](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46099124041) | V786 original_return=1, queue=1, abi=1, lane=0, timer=0, deferred=0. Handler return remains 0 |
| Original callback entry and compiler save | [46099124041](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46099124041) | V807 original_prologue=1, save_return=1, 8 original stack writes, 13 observed visits, ordinal=6. Stop before callback continuation |

The full-image owner-original Windows native executable is a linked PE32+
AMD64 running actual original translated game code with the pinned NWiiRecomp
runtime and private authenticated Wii inputs. The V756 complete-image
callback-prefix result above **succeeded**, not merely passed source tests.
Its terminal authenticated summary is:

~~~text
V756_WINDOWS_CALLBACK_PREFIX exit=zero alarm_return_verified=1 callback_prefix_verified=1 ordinal=6 original_prologue=1 compiler_save=1 continuation_executed=0 callback_return=0 handler_return=0 boot_verified=0
~~~

This is a substantial original-game startup milestone but **not** a game
boot. No complete callback or interrupt return, native game main, graphics
frame, frontend or gameplay has been verified.

## Implemented continuous-next Windows steps (awaiting original-image owner results)

These modes are not arbitrary instruction-count milestones. They run
further original game initialization and Wii service behavior in the
complete Windows executable, with a precise stop when the next original
hardware call is not yet admitted.

| Mode or stage | Original code to execute | Windows evidence as of this ledger |
| --- | --- | --- |
| --owner-callback-time | V813: original callback continuation through authentic OS time helper + leaf returns; V822 exact-time census | [46101497609](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46101497609) 24/24 source/integration passed; original execution pending |
| --owner-callback-frontier | V831: original post-time callback continuation through its wireless-service branch, stopping **before** the wireless callee | [46101682908](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46101682908) 30/30 source/integration passed; original execution pending |
| --owner-progression-matrix | Compile one complete Windows PE and relaunch with fresh state for eleven successively enabled native SI, handler, callback, wireless and handler-return stops | [46103926739](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103926739) source and integration tests passed at `a7e73b9`; owner-original 11-stage run still needed. Every step has its own strict validation and fails at the first incorrect gate |

The old single-build [46099124041](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46099124041)
already proved callback prefix in one complete original Windows executable.
The newer progression matrix must independently prove all later bounds
before its additional results can be reported as original executed.

## Later verified checkpoints (November 28, 2026)

- [46100488015](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46100488015): original-owner Windows single-image pipeline passed its **five** authenticated SI/callback-prefix stages. Repeated launches used one compiled PE. This does not establish a callback return, handler return or native boot.
- [46103388951](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103388951) (V923) and [46103389001](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103389001) (V933): owner-original Linux focused harnesses passed native handler-return / RFI checks in split and non-split configurations, eight valid trials each. Their resume/vector boundaries were synthetic and they do **not** authenticate a continuous Windows boot.
- [46103926739](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103926739): the expanded **eleven-stage Windows source/integration regression** passed, including fail-closed callback and handler-return output checks. The predecessor [46103731727](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103731727) failed on stale ten-stage test assumptions, and [46103875745](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103875745) caught a Python line-break regression; both were fixed before this passing run.
- The V763 full-image handler-return stage is **implemented but not owner-original Windows verified**. The Linux native RFI fixture is a reference implementation, not evidence that the Windows single-image pipeline has reached RFI, OSInit resumption or main. Check the owner-original Windows workflow's redacted stage evidence before advancing this ledger.

## Windows complete-image RFI dependency translation (new preflight)

Commits [a3329ab](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/a3329abdfeca71a02f3334c12bc7cdee01ede1d4),
[48aacd5](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/48aacd5b6f7257fa8afa90720c55e4103ecab87a),
[fc0cd88](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/fc0cd888b1645e5e59a0b5f3829af78a185cc40e)
and [4d0ef1d](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/4d0ef1d27b0bccd03904798f41129f0abf733fc7)
prepare the original dispatcher-to-RFI dependencies in the deepest Windows
full-image translation. This is intentionally **not** a new execution gate.

- The original handler-return mode now passes `--epilogue` to the authenticated
  SI analyzer, including the original scheduler enable, reschedule and
  54-word context-loader ending in `rfi`. Earlier modes retain their
  original analyzer roots and stop conditions.
- The read-only V921 native audit checks unique original function/label
  ownership, direct dispatcher and scheduler edges, the terminal native
  RFI source label, and absence of interpreter fallback in audited labels.
  The focused V923 owner fixture remains a separate execution result.
- The original-free [46104222828](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222828)
  Windows progression/source workflow passed at `fc0cd88`. Later V921
  overlap/refusal hardening at `4d0ef1d` must not be called CI-verified until
  its own checks finish.
- The owner-original Windows progression must report the redacted
  `V921_WINDOWS_DISPATCHER_PREFLIGHT verified=1` marker before the
  native link and eleven-stage execution matrix can qualify at this head.
  A V921 failure is a translation/preflight failure, **not** an observed
  guest RFI fault. Even a V921 pass proves code coverage only. Original
  handler return, RFI, OSInit resumption and main each require their own
  authenticated execution evidence.

## Original Windows scheduler-enable entry, next authenticated boundary

The native Windows continuation now has an **opt-in twelfth execution gate**,
which runs after the original SI handler BLR and resumed dispatcher.

- [94ecf5a](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/94ecf5a6a177887aeb18234ffbfde75949997e89) installs a checked
  original-dispatcher branch handoff that must reach the first generated
  instruction tick of the original scheduler-enable function. It tracks
  the same CPU, link register, native instruction count, stack, r2/r13,
  MSR, unchanged service state, and exact original word identity.
- [919b46c](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/919b46c40358921413fb5ede1e232e2ae23a15d7) makes the observer part of
  the full translated image, disabled for all earlier execution stages.
- [19fec08](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/19fec08c160c59b9e8d6aead9e5b74d9f2764bba)
  adds the twelfth same-executable stage and strict log verification.
- [d8c552b](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/d8c552b3fd83f30a208b0d73706b83ec2ac6e922)
  updates the earlier native-RFI source regression to recognize this
  additional post-V920 observer.
- [46105889638](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46105889638)
  **passed the 12-stage Windows original-free source/integration suite**.
  It establishes correct composition, ordering and refusal behavior with
  test logs, not twelve executed original-owner Windows checkpoints.

The new terminal marker `V922_SCHEDULER_ENTRY` must be emitted by the
real private Windows executable and pass the new strict V922 auditor
before claiming an original scheduler call. The native scheduler leaf's
return, subsequent reschedule, original context loader and `rfi` still
require separate continuous owner-original execution evidence.

## Technical next actions, in dependency order

1. **Verify the owner-original V758/V759 branches** of the same compiled
   Windows image. If the private observer refuses, use the first
   V813_CALLBACK_TIME_INVALID or V831_CALLBACK_FRONTIER_INVALID evidence,
   then repair the actual native call, CPU state or runtime service.
2. **Implement and exercise actual wireless dependency/return** with the
   existing authenticated V847 wrapper and V861/863 EXI write integration
   when required. Reuse existing original code and never replace a missing
   EXI service with a fake successful return. Verify callback return with
   the V850 source/ABI/dispatcher witnesses only after its predecessor.
3. **Continue through the original handler BLR and dispatcher resume**
   using existing V868/V920 code, then RFI and saved Wii context through
   the existing V921/V922 components. Those Linux original-image
   implementations still need authentic Windows composition and proof.
4. **Resume OSInit and return toward game main** via V928's original
   interrupt-enable helper return. Original static audit identifies
   __start at 0x8000403C, OSInit at 0x80520670, the main call at
   0x800041A0 and main at 0x802D3F40. The presence of these symbol
   addresses in the image is not execution evidence.
5. After entering original main, address whichever genuine DVD/IOS,
   filesystem, memory, threading, video (VI/GX), audio and controller
   services it needs. First native frame, frontend and gameplay require
   their own verified runtime observations.

No isolated instruction-count increases without an actual failing
instruction requiring a focused regression. Preserve private DOL/ELF,
assets, translated game C++, original binaries and raw owner execution
traces outside Git. Keep PR #36 draft until authentic boot milestones.
