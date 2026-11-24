# Boot-first native recompilation loop (source-only tooling)

## V415: complete-image native link lane (independent of NAND startup)

The authenticated November 17 whole-image run
[43996721127](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/43996721127)
prepared 27,941 ELF function symbols, generated 112 C++ shards and passed
113/113 syntax checks. It did not link or launch a complete executable.

The whole-image workflow now has a third scope, `link`. After all
syntax checks it configures the generated NWiiRecomp project with its
pinned runtime, builds the complete `UndercoverWiiLocal` target and
validates a Linux x64 ELF executable without launching it. No original
game output, translated code, native binary or private compiler log is
published. The existing owner-private authorization variable still gates
the original-image job. On push the full link runs only if one of the
two build scripts changes; normal NAND iteration does not trigger it.
Manual workflow dispatch can choose `sample`, `all`, `link` or `startup`.

Original-free integration tests compile a synthetic executable, check
that it is never launched, reject unresolved symbols and preserve an
existing build directory. This lane is not yet a native Windows
executable or a verified full-game launch. The generated upstream runtime
also has not yet been integrated with all of the custom NAND host services.

The November 24 authenticated [V415 run 45302858172](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45302858172)
translated 112 shards, passed 113/113 syntax checks, configured and linked
the entire Linux x64 executable, and verified its ELF format. The output
gate was `linked=1 platform=linux-x64 launch=0 boot_verified=0`.
This is a verified complete-image native link, not a Windows build or boot.

### V419: independent bounded complete-image startup candidate

The new `startup` scope preserves the uninstrumented V415 link-only
control. It SHA-verifies the original DOL, checks both entry-point linked
branches and the complete register-initialization function, derives
private word expectations, and requires the three actual generated AOT
trace seams. It patches only runtime observers, not the translated game
shards. The isolated headless process must execute the original entry,
enter register initialization with the correct LR, and reach the hardware
initializer with all 32 GPRs matching the independently established V16
register results. It terminates before executing the hardware body.
Interpreter fallback and invalid witness stages fail the gate; only three
ordered valid stages, the final success marker and exit zero pass.
No assets/FST are staged, no proprietary binary/log is uploaded, and the
custom V418 IOS transport is not activated in this candidate. A successful
owner result would establish only bounded original register initialization
in the complete linked image, not complete continuous startup.
Local source-only tests and a synthetic process witness passed. Owner
validation remains pending.

## November 24, 2026: authenticated 96-call NAND frontier

V412 [owner run 45297574228](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45297574228)
verified all 16 original Wii AOT trials at the 96-call boundary after the
guest-selected ISFS callback, with exit code zero and all inherited trial
assertions intact. V411 identified host stop site 12 at call 50. V412
proved that site belonged to the old V260 64-call post-IPC discovery
observer, retiring its stop only after authenticated NAND/ISFS progress.
The 24-, 48- and 50-call controls were preserved.

```text
V412_EXIT_CENSUS rc=0 ... entries=16 max_calls=96 last_calls=96 guest_stop_trials=16 running_trials=0 mapped_trials=16 v390_trials=16 classified=1 boot_verified=0
V412_OWNER_RESULT_GATE verified=1 retired_trials=16 boot_verified=0
```

V413 is an independent candidate targeting 192 original function entries,
with a separate 96-call prefix witness. It snapshots the guest-selected
OSContext at the original dispatcher OSLoadContext entry and compares
PC, MSR, GPRs, LR, CTR and XER at the first natural successor matching the
saved PC. It checks IRQ coherence without changing guest state or IOS
behavior. A separate gate distinguishes bounded execution, exact context
restoration, and restoration of the interrupted PC/MSR. The latter two
are now verified for NAND in all 16 original trials, with exit code zero
and 192 counted entries ([owner run 45299374133](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45299374133)).
This is an exact restoration witness, not direct instruction-level proof
of RFI, nor proof of full boot or game main.

V414 records every counted original AOT entry after that restoration,
including the final observed (not necessarily executed) boundary, in private
scratch. Each entry is checked against the SHA-pinned owner DOL and ELF
function extent; a tail window for interior entries is not a whole-function
proof. The earliest non-authentic span is repaired only if it is an exact
complete NOP-only ELF function of 16–8192 bytes. The private candidate must
round-trip byte-for-byte, preserving all other sections. If prepared, it
is independently retranslated, compiled, linked and executed against the
same V413 gates. Unknown or mixed spans are never automatically changed.
The authenticated V414 owner run
[45301607068](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45301607068)
passed all 16 trials. It recorded 2,800 post-restoration entries (175 per
trial), with only three distinct addresses and all three observed spans
matching the original DOL. No repair was applicable. This is a bounded
entry-span result, not a claim that every executed instruction in the
reduced fixture is authentic.

V416 independently repeats that control and records the PC/LR route,
instruction counter, timebase, decrementer expiry, native IOS request and
reply queue, PPCCTRL X1/Y1/Y2, Hollywood flag, IRQ level, EE, interrupt
eligibility and reply-header status at the observed call boundaries.
The audit detects repeated suffixes of up to 12 calls and aggregates
already identified SDK entry categories; unrecognized targets are
reported as other. It never pumps IOS, changes time, delivers an IRQ,
alters guest state, or emits addresses and register values publicly.
A recurring route is not by itself a proof of a deadlock. The authenticated
[V416 run 45303254206](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45303254206)
observed the same three-call cycle in all 16 trials, 2,800 entries, advancing
instruction counter and timebase, no expired decrementer, no pending IOS
requests/replies, and no active IRQ. The recorded reply headers were not
negative. Two targets classify as interrupt disable/restore; the third
was unclassified. This resembles the previously studied SYSCONF retry
loop, but the precise PC/LR identities and live status byte still need
verification. Do not fabricate a status transition or force timer/IRQ
progress.

### V420: actual callback and live callsite provenance

V414 authenticated only the post-restoration successor spans. V420 keeps
the V416 control, then records the selected callback entry and all 192
counted successors in a separate native process. The private observer
classifies the known SDA SYSCONF status, callback input sign, live entry
word and live LR-minus-four word. The private audit compares the latter
two words independently against the owner DOL and actual reduced fixture,
including caller words in functions that were not observed at entry.
It checks the historical V263 exact PC/LR route, counts status-writer
entries before restoration, and validates all resumed entries against
V416's own trace. The observer does not alter guest state.

Only the first non-authentic, complete NOP-only entry span may be repaired
with original bytes, and only if the live first word also agrees with
the fixture. The candidate must round-trip exactly. If applicable the
runner independently regenerates, compiles, links and tests it. A mixed,
missing or ambiguous span remains diagnostic; no SC state or IOS result
is forced. All addresses, raw instruction words, code and candidate
binaries remain in owner-private scratch. The authenticated
[V420 run 45306037053](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45306037053)
found 12 distinct pre-restoration entries, 11 original spans and one
NOP-only span. All 16 trials confirmed the exact SC retry route with
status 1, no observed status 3 or known writer entry. Live text did
not agree with either file; the existing reduced harness explicitly
does not load all original text into guest RAM.

### V424: restore the unique observed AOT placeholder

Keep V420 unchanged as the control. V424 authenticates the original
DOL and ELF, requires the same single all-NOP span in each complete
trial, resolves its exact or unique interior ELF extent and confirms
its actual generated trace and dispatch entry. Restore only that
bounded span, require a byte-for-byte reversible installation and
regenerate the private candidate. The live RAM text mismatch is not
used as a gate because the reduced loader omits most text. The
candidate audit requires the same emitted entry and reports partial
or complete trial progress, observed SC state 3, return-context
witness and the old retry route. It never forces a state change or
claims boot. All five local synthetic tests passed; owner validation
is pending.

Original-free tests:

```sh
python3 -m unittest discover -s research/native_recomp -p 'test_v413_nand_context_resume.py' -v
```

## November 23, 2026: NAND IPC checkpoint and next guest frontier

**Do not conflate test lanes.** This runbook's historical V51 continuous
`__start` result and the later owner-original authenticated NAND candidate
are different bounded execution paths. The NAND candidate is not proof of
complete `__start` -> `main` or a game boot.

Authenticated owner-original V370/V371 (run
[45107293227](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45107293227))
verified genuine NAND IPC X1 intake, native IOS ACK, and one guest
Hollywood `PPC_FLAG` IPC write-one-to-clear:

```text
V370_FLAG_CENSUS writes=1 accepted=1 ipc_write=1 cleared=1 retained_any=0 queued_any=1 irq_any=0
```

This confirms that the original flag was cleared **without dropping the
queued reply**. It does not confirm a completed Y1 reply, actual external
exception delivery, IRQ handler return, SC status transition, `main`, or
rendering. The first V365 sixteen post-ACK samples had a verified installed
vector and safe guest dispatch state, but no MSR.EE-eligible interrupt.

The next legacy failure, public assertion 0716, is V153's earlier first-
SYSCONF file-open *trial-end* proof. Do not interpret that historical test
condition as hardware failure or suppress guest code. V372 scopes only the
identified V153 proof after verified NAND entry; it leaves the original
SC-only lane's check intact and records bounded mailbox state. The first
owner V372 attempts failed closed at harness source matching and did not
establish further guest execution. The updated V372 matcher and V373
timeline still require owner-original validation.

V373 extends read-only census from 16 IRQ-asserted calls to 96 guest calls
with an outstanding native IOS reply, including MSR.EE-disabled/masked
intervals. It emits only bounded boolean fields, first-eligible indices,
and no guest PCs, register contents, assets, or translated code. It does
not pump Starlet, force IRQ entry, or manufacture Y1.

Source-only regression commands (not original-game execution):

```sh
python3 -m unittest discover -s research/native_recomp -p 'test_v372_nand_v153_trial_scope.py' -v
python3 -m unittest discover -s research/native_recomp -p 'test_v372_nand_sc_trial_audit.py' -v
python3 -m unittest discover -s research/native_recomp -p 'test_v373_nand_irq_timeline.py' -v
python3 -m unittest discover -s research/native_recomp -p 'test_v373_nand_irq_timeline_audit.py' -v
```

Authenticated follow-up: [Wii V298 NAND owner workflow](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/workflows/wii-v298-scoped-nand.yml). Require its actual
owner-original output before advancing this checkpoint. Public source-only
and standalone native IOS bus tests prove different, narrower properties.

## Why this exists

As of November 17, 2026, the pinned original Wii executable is verified
through **continuous native V51 at `0x805208C4`**, starting from genuine
`__start` at `0x8000403C`. The path uses NWiiRecomp AOT-generated native
C++ and includes original `OSExceptionInit` (15 vectors plus
`_restgpr_20`), `__OSInitSystemCall` (the authentic 28-byte handler at
`0x80000C00` and 83 cache lines), `__OSInitAlarm`/shutdown list,
`__OSModuleInit`, `__OSInterruptInit`, original seven-bank
`SetInterruptMask`, the complete interrupt return into `OSInit`,
`__OSContextInit`, and a **second native call to the same original
`__OSCacheInit`** function earlier invoked during `__start`.

V51 verifies both original cache callsites and the second guest return LR
`0x805208C4`, preserving the OSInit stack ABI. The SHA-verified
owner-original 16-trial native tests and independent synthetic tests passed
[GitHub Actions run 44190097982](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44190097982).
Earlier V50 `0x805208C0` was verified in
[run 44185965547](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44185965547);
V49 returned from interrupt initialization at `0x805208BC`; V48
completed its seven-bank mask loop at `0x805266AC`; V47 executed the
IRQ-disable/mask preparation at `0x80526698`.
These are bounded native original-code execution milestones, **not** a
complete game boot. Guest PCs need not increase monotonically across calls.

**Remaining emulation boundary:** the interrupt-controller MMIO callbacks
provide deterministic test-only read/write values and traces, not a working
PI/IOS hardware device. Debug printing and selected OS services are still
test-only callbacks. Original game binaries and generated translated game
C++ are kept in private ephemeral CI directories.

The separately verified V68 **direct-entry** `OSInit` regression reaches
EXI initialization at `0x804EFA34`. It is not continuous original
`__start` execution. Neither lane has reached original game `main`,
a rendered frame, the frontend, or playable gameplay.

**Next blocker:** the original `OSInit` call at `0x805208C4` reaches
`EXIInit` at `0x804EF9BC`. Reuse the exact owner-original direct-entry
V65/V66/V68 EXI polling/call-graph guards while adding a bounded V52
continuous-start test. Implement missing EXI/PI/IOS device semantics only
as required, and do not conflate controlled hardware callbacks with real
device emulation.

## Source-only checkpoint and regression driver

`boot_progress.py` is a local command wrapper. It can execute an existing
owner-private build/test runner while writing an atomic, minimal JSON result.
It records the command's return code, pass-marker count, elapsed time,
optional observed guest entry/PC/stage, and an output checksum on failure. It
**does not** store the command, paths, raw stdout/stderr, source DOL, or game-
derived generated C++ in its result.

To test an existing original-code runner **without fabricating a checkpoint**:

```sh
python3 research/native_recomp/boot_progress.py \
  --lane osinit-direct --report /private/boot-results/current.json \
  --timeout 600 --dol /private/owner.dol.bin \
  --sha256 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 \
  -- bash research/native_recomp/run_osinit_eximask_v68.sh /private/NWiiRecomp-master /private/owner.dol.bin
```

Failed runners cannot publish verified `observed_pc` or `stage` fields even if
an early marker appeared before a failure or timeout. The driver rejects report
paths that alias a pinned input or baseline, validates baseline schema and lane,
and prohibits comparison across different pinned owner-image hashes.

A successful legacy test with no instrumentation receives status
`passed_uninstrumented`, **not** a proven new PC. Add this exact marker to a
native test *only after it checked the actual final `ctx.pc` and entry*:

```
PASS: native original __start assertions
BOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26
```

The `stage` is an **explicit, monotonic, test-defined execution checkpoint**,
not the release version or a numeric sort of guest addresses. Reentrant or
higher-address branches can make raw PC comparison misleading. For a later
validated run, supply `--baseline` and `--require-progress` to reject any
unchanged/regressed stage or stop PC. Never compare the `osinit-direct` and
`continuous-start` lanes.

Synthetic source-only driver tests:

```sh
python3 -m unittest discover -s research/native_recomp -p test_boot_progress.py -v
```

## CI and privacy limits

`.github/workflows/native-recomp-source-checks.yml` runs standard-library
checkpoint-driver unit tests, Python syntax checks and shell syntax checks,
without owner game assets. It **cannot** execute the proprietary original DOL,
prove a new boot checkpoint, or substitute for native ASan/UBSan tests.

Do not upload runtime logs, private DOL/ELF, game assets, recompiled game-code
output or private fixture slices to CI. Only independently written source and
safe test-result summaries may enter GitHub. Always inspect the exact
branch/PR SHA before committing, and use regression checks before extending
how far original `__start` executes.
