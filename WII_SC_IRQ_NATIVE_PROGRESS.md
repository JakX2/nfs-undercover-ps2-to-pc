# Wii SC IRQ native continuation: V141-V145

Status: **five verified owner-original native checkpoints** through V145.
V146 is an experimental original IPC first-leaf execution checkpoint and is
not verified until the owner-original native trial passes.

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

## Next frontier: original IPC IRQ delivery

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

V146 targets the first original helper call from inside the registered IPC
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
- **Not verified:** SC reply consumption, release of the OSInit retry,
  complete Nintendo OS bootstrap, original `main`, Windows game window,
  first rendered frame, frontend, gameplay, audio or feature parity.

Reproduce the relevant stage from GitHub Actions by manually dispatching
`wii-v141-sc-vector.yml`, `wii-v142-sc-dispatch.yml`,
`wii-v143-sc-time.yml`, `wii-v144-sc-disable.yml` or `wii-v145-sc-ipc.yml` on
`research/wii-native-recomp-preflight`. Private owner-staging requires the
preconfigured DOL/ELF ID secrets and the private-enable repository variable.
The workflows erase owner binaries and generated translation after execution;
public logs must remain bounded to summary and original-free checkpoints.
