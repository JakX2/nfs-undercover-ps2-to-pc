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
| Original callback entry and compiler save | [46099124041](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46099124041) | V807 original_prologue=1, save_return=1, 8 original stack writes, 13 observed visits, ordinal=6. Early stop only |
| Original callback time and wireless branch | [46104222792](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792) | Original time helper returned; callback reached wireless ordinal 3 and entered its wrapper |
| Original wireless EXI transaction | [46104222792](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792) | Original changed wireless path; 12 native EXI transfers, 44 bytes, 3187 observed visits, 74 polls and 52 MMIO operations |
| Original callback ABI return | [46104222792](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792) | V762 changed=1, suffix_boundary=13, callback_return=1, outer_dispatch=1; not handler return |
| Original SI handler BLR and resumed dispatcher | [46104222792](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792) | V763 handler_suffix=1 and handler_return=1; original scheduler and RFI have not executed in this result |

The full-image owner-original Windows native executable is a linked PE32+
AMD64 running actual original translated game code with the pinned NWiiRecomp
runtime and private authenticated Wii inputs. The V756 complete-image
callback-prefix result above **succeeded**, not merely passed source tests.
Its terminal authenticated summary is:

~~~text
V756_WINDOWS_CALLBACK_PREFIX exit=zero alarm_return_verified=1 callback_prefix_verified=1 ordinal=6 original_prologue=1 compiler_save=1 continuation_executed=0 callback_return=0 handler_return=0 boot_verified=0
~~~

The earlier V756 checkpoint was not a complete callback return. The later
owner-original Windows run **does** verify the callback ABI return and
SI handler BLR, as recorded above. It remains **not** a game boot:
native scheduler return, context-loader RFI, OSInit resumption, main,
graphics frame, frontend and gameplay are not verified.

## Implemented continuous-next Windows steps (awaiting original-image owner results)

These modes are not arbitrary instruction-count milestones. They run
further original game initialization and Wii service behavior in the
complete Windows executable, with a precise stop when the next original
hardware call is not yet admitted.

| Mode or stage | Original code to execute | Windows evidence as of this ledger |
| --- | --- | --- |
| --owner-callback-time | V813: original callback continuation through OS time helper and leaves | Owner-original verified by the later combined [11-stage run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792) |
| --owner-callback-frontier | V831: original callback wireless branch, before the wireless callee | Owner-original verified by the same combined run |
| --owner-progression-matrix | Compile one complete Windows PE and relaunch with fresh state through **13 staged native boundaries** | [46104222792](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792) proves all **11 original-owner Windows stages** through handler return. [46108297939](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46108297939) proves the **13-stage original-free CI source suite**, not owner execution of all 13. Scheduler entry and scheduler return are still awaiting owner-original results |

The old single-build [46099124041](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46099124041)
already proved callback prefix in one complete original Windows executable.
The newer progression matrix has now independently verified the original
callback and handler return. The two scheduler stages are not yet independently
owner-original verified. Each stage has its own strict log auditor and
relaunches the **same compiled** complete-image Windows binary with fresh state.

## Later verified checkpoints (November 28, 2026)

- [46100488015](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46100488015): original-owner Windows single-image pipeline passed its **five** authenticated SI/callback-prefix stages. Repeated launches used one compiled PE. This does not establish a callback return, handler return or native boot.
- [46103388951](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103388951) (V923) and [46103389001](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103389001) (V933): owner-original Linux focused harnesses passed native handler-return / RFI checks in split and non-split configurations, eight valid trials each. Their resume/vector boundaries were synthetic and they do **not** authenticate a continuous Windows boot.
- [46103926739](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103926739): the expanded **eleven-stage Windows source/integration regression** passed, including fail-closed callback and handler-return output checks. The predecessor [46103731727](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103731727) failed on stale ten-stage test assumptions, and [46103875745](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46103875745) caught a Python line-break regression; both were fixed before this passing run.
- [46104222792](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792), owner-original Windows **passed all 11 stages**, with `V921_WINDOWS_DISPATCHER_PREFLIGHT verified=1`, native PE link, and terminal `V757_WINDOWS_PROGRESSION completed=11 full_image=1 compiler_reused=1 native=1 handler_return=1 rfi=0 boot_verified=0`. The scheduler and RFI roots were verified as generated code but not executed by this result. The focused Linux native RFI fixture is still separate evidence, not proof of continuous Windows RFI, OSInit resumption or main.

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
  overlap/refusal hardening also passed on `4d0ef1d` in
  [46104624617](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104624617).
- The owner-original Windows [11-stage run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46104222792)
  emitted the redacted `V921_WINDOWS_DISPATCHER_PREFLIGHT` success before
  linking and executing. This source audit proves the native scheduler and
  RFI loader exist in the image. Its V763 result independently proves the
  original handler returned. Scheduler enable/return, RFI, OSInit and main
  still require owner execution proof.

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

The V922 scheduler-entry marker must be emitted by the owner-original
Windows image and pass its strict V922 auditor before claiming an original
scheduler call. The follow-on V923 scheduler-return gate, comprising the
original disable/restore callees, still requires the same evidence.

The [13-stage Windows source/integration suite](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46108297939)
passed with commit `e7971fa`. It includes host-side preparation of
deep-only V922/V923 flags, twelve predecessors, and final V923 refusal
tests. The original owner run [46105889593](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46105889593)
was still in progress at the time of this ledger revision; do not infer
scheduler execution from the source suite or a running workflow.

## Original reschedule continuation, private Windows owner verification pending

The translated full Windows executable now installs original scheduler
enable/disable/restore and original rescheduling as one code path. These
are authentic original-function boundaries, **not** arbitrary instruction
count targets:

- V922: original dispatcher branches into the generated native scheduler
  enable function and reaches its first original instruction tick.
- V923: original scheduler enable executes its disable/restore callees,
  updates the original nesting counter and returns to the dispatcher.
- V924: original dispatcher calls the original reschedule function, whose
  first native instruction tick is authenticated.
- V925: no-thread-switch reschedule follows original branch/return and
  reaches the dispatcher at the original context argument instruction.
  A nonzero scheduling hint is explicitly **unadmitted**. This mode does not
  pretend the thread switch returned, nor execute the context loader or RFI.

All four modes are strictly ordered, default disabled for earlier runs and
audited against the original native compiled source labels and ABI state.
The [15-stage Windows original-free source/integration workflow 46109586905](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46109586905)
passed at `0f39c67`. It is not owner-original 15-stage execution proof.

The first twelve-stage owner-original attempt,
[46105889593](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46105889593),
**failed after successful original translation, native scheduler observer
installation, V921 code-coverage preflight and native Windows link**, but
**before the first stage launch** with `V426_WINDOWS_FAILED reason=host_error`.
The original-free progression environment had gained an additional required
scheduler flag that the owner launcher did not supply. This was corrected in
[e7971fa](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/e7971fa86117f5628b0baf85fbb6e3b0263365e9).
[cedab4e](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/cedab4e485fb713132b25c83ac67869a2a61280b)
now validates the complete progression contract **before native compilation**
and emits the redacted `progression_environment` refusal if invalid.

The later private owner-original
[46108297899](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46108297899)
was still in progress at the time of this ledger update. No original Windows
scheduler entry, return, reschedule or RFI should be marked verified without
its completed original-owner execution markers.

## Technical next actions, in dependency order

1. **Verify the owner-original V922–V925 scheduler and reschedule stages** in the complete
   native Windows executable. Use only the first redacted refusal marker
   to fix actual CPU state, instruction translation or Wii service behavior.
2. **Continue from original scheduler return into reschedule and context
   restore**, reusing the original authenticated native RFI loader and
   the independently verified focused V923/V933/V935/V946 harnesses.
   Preserve real interrupt state and do not synthesize a context return
   in the complete Windows executable.
3. **Execute and verify the actual PowerPC `rfi`** in the same Windows
   startup flow, then resume original OSInit rather than stopping at an
   artificial success marker.
4. **Resume OSInit toward main** via the V928 original interrupt-enable
   helper. Previous static audit identifies __start at 0x8000403C,
   OSInit at 0x80520670, the main call at 0x800041A0 and main at
   0x802D3F40. Symbol identity is not evidence that those instructions ran.
5. After real main entry, implement the next observed DVD/IOS, filesystem,
   memory, threading, VI/GX, audio and input dependencies; verify the first
   native frame, frontend and gameplay separately.

No isolated instruction-count increases without an actual failing
instruction requiring a focused regression. Preserve private DOL/ELF,
assets, translated game C++, original binaries and raw owner execution
traces outside Git. Keep PR #36 draft until authentic boot milestones.
