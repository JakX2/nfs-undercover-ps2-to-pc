# Windows owner-original Wii startup frontier, 2026-11-28

Branch: `research/wii-native-recomp-preflight` (draft PR #36).
This records observed **complete-image Windows x64** execution separately from
Linux isolated owner-original AOT probes and original-free Windows test fixtures.
A passing source-only unit test does not mean the underlying game path ran.

## Last verified Windows milestones

| Stage | Owner Windows evidence | Verified behavior | Next unexecuted boundary |
| --- | --- | --- | --- |
| V750, post-time guard | [run 46095473544](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46095473544) | Complete translated native Windows PE linked/launched. Original third system-time helper returned. Fourth linked SI call authentically refused (ordinal 4, kind 1) | Original fourth-call instruction |
| V751, transfer prefix | [run 46096246382](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46096246382) | Complete Windows PE linked/launched. Original `__SITransfer` entry, GPR-save and interrupt-disable prefix with 20 authenticated visits | First unadmitted transfer call/MMIO |

The V750 exit was a planned *refusal*, not a successful SI transfer. The
V751 exit was a planned zero-exit *before MMIO*, not a transfer return.
Both carry `boot_verified=0`. The executable runs translated original logic
natively, but it does not reach original game `main`.

## New stages: composed and source-tested, not yet Windows owner-executed

The owner-private original installers build on V742 in this exact order.

| CLI mode | Existing native installer chain | Proof needed |
| --- | --- | --- |
| `--owner-transfer-return` | V768, V777 | Fourth original transfer returns through real device and ABI restore, no caller instruction |
| `--owner-transfer-suffix` | V768, V777, V778 | Handler resumes until next refused call or BLR |
| `--owner-alarm-return` | V768, V777, V778, V786 | Fifth original alarm cancellation returns |
| `--owner-alarm-suffix` | V768, V777, V778, V786, V789 | Classify exact subsequent original handler branch before execution |
| `--owner-callback-prefix` | V768, V777, V778, V786, V789, V807 | Authenticate original callback bctrl entry, native prologue, compiler save, strict pre-continuation stop |

All require `--owner-scope os-si-handler-time`, pinned original owner DOL/ELF
and the exact pinned NWiiRecomp checkout. Every mode is mutually exclusive,
has its own installer order, env flags, analyzer roots and strict log auditor.
Unexpected raw tail markers, failure codes and timeouts must not pass.

Focused source-only workflows at the recorded versions:

- V754 Windows alarm return: [run 46097541177](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46097541177), **12/12 passed**.
- V755 Windows alarm suffix: [run 46098038788](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46098038788), **16/16 passed**.
- V756 Windows callback prefix: [run 46098227345](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46098227345), **15/15 passed**.

Isolated original-owner V754 alarm cancellation also passed
[run 46097541073](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46097541073)
(split/non-split). This is not a full-image Windows fifth-call return.

## Next gated actions

1. **Keep the Windows execution frontier at V751** until the original-private
   `owner-return-windows` job of `wii-v751-windows-transfer-prefix.yml` proves
   the complete V777 SI transaction, IRQ/compiler restores and original ABI
   return with `boot_verified=0`.
2. Run the V753 owner Windows suffix, then verify the exact next handler
   boundary. Never infer a full transfer from a source-only or isolated test.
3. Only after V752 and V753 pass, run the opt-in owner-private V754, V755
   and V756 workflows in order. Fix native execution failures before adding
   further original calls.
4. Keep owner executables, private code, resource archives, generated game C++
   and raw owner traces out of Git; CI must delete all private temporary files.
5. The game's original `main`, first frame, frontend and gameplay remain
   **unverified**. Keep PR #36 draft.

This is native ahead-of-time recompilation with bounded runtime witnesses,
not Dolphin/PCSX2, not a fully booted game, and not a playable PC port.
