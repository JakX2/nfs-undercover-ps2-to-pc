# Wii SC IRQ native continuation: V141-V194

Status: **V194 owner-original PowerPC checkpoint verified (16/16 trials)**.
V195 is an experimental hardware IRQ-entry checkpoint and is **not verified**
until its separate owner-original test passes. This document retains the earlier V141-V145
checkpoints as historical evidence, not as the current development frontier.

## Latest verified Wii PowerPC execution (2026-11-21)

The second original Wii `IOS_Open` request reached the native host IOS
scheduler after Broadway submitted it through the real guest IPC path.
The native IOS transport now distinguishes a *captured request intake*
from the writable live `X1` MMIO bit, retains the submitted physical pointer
until Starlet ACK, and defers completion delivery until the guest acknowledges
`Y2` and clears the Hollywood IPC interrupt cause.

| Milestone | Authenticated owner-native evidence | Result |
|---|---|---|
| V183 | [16-trial run 44844951023](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44844951023) | A second IPC request was submitted through the genuine original guest path, enabling eight additional translated PPC call entries without a synthetic IOS reply. |
| V184 | [16-trial run 44845800535](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44845800535) | Six more translated PPC calls; the second IOS request remained an authentic `IOS_Open`. |
| V185 | [16-trial run 44846147043](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44846147043) | Original guest execution reached `PC=0x80529434 / LR=0x80526CB0`, the native IOS yield boundary, with no reply yet queued. |
| V186 | Native second-request owner-original trial; see `wii-v186-second-ios-ack.yml` | One genuine second-request Starlet `Y2` ACK, Hollywood IRQ, one queued completion, no guest CPU mutation or fabricated reply. |
| V187-V188 | Original PPC scheduling / OSDI trials; see dedicated versioned workflows | Genuine original handler calls after the second IOS ACK, preserving the pending reply and masked IRQ state. |
| V189 | [16-trial run 44851180151](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44851180151) | Original interrupt-restore helper reached `PC=0x80529940 / LR=0x80526CB4` with SC readiness still 1. |
| V190 | [16-trial run 44852816608](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44852816608) | Authentic rescheduler entered `PC=0x805229B4 / LR=0x80526CBC`; `Y2=1`, IRQ flag=1, one genuine second IOS completion queued, guest state coherent, SC=1, MSR.EE=0. |
| V191 | [16-trial run 44856455287](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44856455287) | Original PPC resumed from `0x805229B4` and reached the authentic OSInit retry helper entry `PC=0x8052F830 / LR=0x80520970`. `SC=1`, `MSR.EE=1`, external exception ready=1, second IOS completion remains queued, and all 16 owner-native/source-only checks passed. |
| V192 | [16-trial run 44856826905](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44856826905) | Executed the original helper at `0x8052F830`; next translated PPC entry was the original interrupt-disable helper at `PC=0x805265AC / LR=0x8052F84C`. Guest `r3=1`, CR0.EQ=1, `SC=1`, `MSR.EE=1`, `Y2=1`, Hollywood IRQ=1, one second IOS completion still queued, 16/16 original-game and public guards passed. |
| V193 | [16-trial run 44857365572](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44857365572) | Executed original `OSDisableInterrupts` at `0x805265AC`, reaching authentic `OSRestoreInterrupts` at `PC=0x805265D4 / LR=0x8052F92C`. `MSR.EE=0`, IRQ-ready=0, `SC=1`, queued second IOS completion=1, Y2/flag=1, `r3=1`, CR0.EQ=0. Both owner original and original-free CI passed. |
| V194 | [16-trial run 44857645514](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44857645514) | Executed original `OSRestoreInterrupts` and returned to **exactly** `PC=0x8052F830 / LR=0x80520970`, the same OSInit retry helper reached in V191. `r3=1`, CR0.EQ=1, SC=1, MSR.EE=1 and IRQ-ready=1. The Y2 Hollywood interrupt and one second IOS completion remained pending, demonstrating a repeatable native OSInit retry cycle. Owner-original 16/16 and public source guards passed. |

**Current authentic guest frontier:** `0x8052F830` (LR `0x80520970`),
after original `OSRestoreInterrupts`. The V191-V194 owner-original trace
proves a closed SC initialization retry cycle with `MSR.EE` alternating
through authentic disable/restore helpers, while the second IOS Y2 IRQ
and a single IOS completion remain queued. The retry is not resolved.

**V195 (unverified):** admit the pending Y2 through the existing native
PowerPC external-exception entry helper only after all V194 original guest
assertions and at the next unexecuted instruction boundary. The hardware
helper validates the original installed exception vector, saves SRR0/SRR1,
and masks EE. This is distinct from executing the original vector/handler,
which must be a subsequent verified milestone; no IOS reply is fabricated.

**Not yet achieved:** final acknowledgment/publication of the *second* IOS
reply, SC status transition to ready, exit from OSInit retry into original
`main`, first frame, frontend, gameplay or a complete Windows port.

The public C++ source-only checkout intentionally lacks NWiiRecomp's generated
CPU/loader headers and private translated Wii game functions. Public tests
compile the independent IOS runtime under C++20 `-Werror` and verify harness
derivation; only owner-original CI can compile/link and execute the complete
translated startup harness. A passing public build is **not** native game boot.


The private test image is constructed from the SHA-256-authenticated owner's Wii
DOL. Original PowerPC instructions are emitted to private temporary native C++
and executed using NWiiRecomp. The public branch contains independently written
host code, original-free source patches and tests only. Do not upload original
executables, extracted instruction words, translated game code or game assets.

## Verified path

| Checkpoint | Guest destination | Owner-native evidence | Meaning |
|---|---|---|---|
| V140 | `0x80000500` | [run 44657890154](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44657890154) | Native IOS SYSCONF ACK raises the installed external exception; CPU SRR state and GPRs are preserved. Test stops before vector execution. |
| V141 | `0x80526CE0` | [run 44659015506](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44659015506) | Original installed PowerPC vector executes and saves interrupted guest state before entering original external exception handler. |
| V142 | `0x80526A3C` | [run 44659554589](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44659554589) | Original exception handler continues into IRQ dispatcher with saved nonvolatile registers, LR, CTR, XER, SRR0 and SRR1. |
| V143 | `0x8052A824` | [run 44659969306](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44659969306) | Dispatcher calls original timebase helper with expected LR, masked MSR and pending IOS request; actual translated native instruction count advances. |
| V144 | `0x805293F8` | [run 44660338019](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44660338019) | Original timebase helper returns and dispatcher enters scheduler-disable helper; native instruction count advances. |
| V145 | `0x80519318` | [run 44662161325](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44662161325) | Original scheduler disable completes; IRQ dispatcher selects registered slot 27 and enters the authentic PowerPC IPC handler with the original exception context and SC IOS ACK still pending. |

All five V141-V145 owner-original runs required **16/16** matching trials, in
addition to preserving prior test gates. Their unit-test companions are invoked
by `.github/workflows/native-recomp-source-checks.yml`.

## Historical V145 to V146 frontier (earlier milestone)

V145 **verified** the registered interrupt-handler entry at `0x80519318`,
IRQ slot 27, after the authentic scheduler-disable routine. The original
dispatcher selected the registered function pointer, preserved its exception
context, and kept the IOS SC acknowledgment genuinely pending.

The V145 native path initially encountered two **harness-only** false
assertions from earlier milestones: V136 treated the later IRQ helper call as
part of its second retry, and V98 still expected idle IOS state after NAND
registration. The scoped corrections preserve those original phase checks and
allow only authentically located scheduler IRQ helper calls to proceed.
No original instruction body or guest status is altered.

At the V145 milestone, V146 targeted the first original helper call from inside the registered IPC
handler. See `.github/workflows/wii-v146-sc-ipc-leaf.yml`. Reaching a helper
is not equivalent to acknowledging the interrupt or completing a reply.

Once selected, the original handler must execute its hardware notification
clear and resume IPC processing. A queued IOS ACK is **not** the same as a guest
reply. The service must publish the actual reply, the original PowerPC guest
must process it, and the original SC status must transition through its verified
code/dataflow before OSInit can escape its retry condition. Do not seed
`r3=0`, override the guest CR0, or manually mark the SC initialization byte
complete.

The original OSInit retry comparison at `0x80520970` compares the helper's
`r3` against `1`. The branch loops while equal. The subsequent
`0x8052BE14` call must be reached by authentic guest control flow, not by a
synthetic skip.

## Verification boundaries

- **Verified:** explicitly bounded execution of owner-authenticated PowerPC
  logic translated to native C++, with original vector/handler/dispatcher
  transitions and test-owned stop instrumentation.
- **Synthetic or host-provided:** Wii IOS guest-memory adapter, SYSCONF fixture,
  device-service steps, host scheduling boundary and native MMIO services.
  These are not a faithful ARM Starlet emulator or complete Wii hardware.
- **Not verified at this historical V145 checkpoint:** SC reply consumption, release of the OSInit retry,
  complete Nintendo OS bootstrap, original `main`, Windows game window,
  first rendered frame, frontend, gameplay, audio or feature parity.

Reproduce the relevant stage from GitHub Actions by manually dispatching
`wii-v141-sc-vector.yml`, `wii-v142-sc-dispatch.yml`,
`wii-v143-sc-time.yml`, `wii-v144-sc-disable.yml` or `wii-v145-sc-ipc.yml` on
`research/wii-native-recomp-preflight`. Private owner-staging requires the
preconfigured DOL/ELF ID secrets and the private-enable repository variable.
The workflows erase owner binaries and generated translation after execution;
public logs must remain bounded to summary and original-free checkpoints.
