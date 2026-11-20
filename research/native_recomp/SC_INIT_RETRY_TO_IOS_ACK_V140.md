# Wii SC startup: native IOS ACK and external vector

Status: V140 owner-original verified, NOT a completed SC initialization or game boot.
Scope: research/wii-native-recomp-preflight, PR #36, 2026-11-20.

This research note contains no game instruction bytes, DOL/ELF slices, assets,
private traces, original NAND content or generated recompiled game C++.

## Verifiable evidence

| Stage | What was proven | GitHub Actions |
| --- | --- | --- |
| V131 | Original SC helper returned r3=1, CR0.eq=1; OSInit retry comparison against 1 at 0x8052096C | [native run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44650454351) |
| V132 | Original helper 0x8052F830 contains an SDA read of -3176(r13), original interrupt calls and status logic | [owner audit](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44651164770) |
| V133 | Guest status byte is mapped, value=1 at retry decision | [native run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44653215850) |
| V134 | Two static direct status reads and eleven direct byte-write candidates; this does not imply execution of those stores | [owner audit](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44653738147) |
| V136 | Two complete original helper retries with authentic interrupt-disable/restore, reached third SC helper call, 16/16 | [native run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44654608279) |
| V137 | Third SC call has IPC X1=1, queued=0, event registered, guest IRQ level=0, MSR.EE=1 | [native run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44655191117) |
| V138 | Original pending guest IPC command=1 IOS_Open for /shared2/sys/SYSCONF in mode=1 (read-only) | [native run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44655915261) |
| V139 | Native IOS ACKed the original SYSCONF open, opened guest file fd, queued reply=1, guest IRQ pending=1, 16/16 | [native run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44657317267) |
| V140 | Authentic external-vector entry at 0x80000500, correct SRR0/SRR1 and preserved GPRs, LR, CTR, XER; reply queued=1, 16/16 | [native run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44657890154) |

## Reusable source-only runtime code

- wii_sysconf_image.h creates a deterministic synthetic 0x4000-byte SCv0
  file containing named setting records, offset entries and SCed footer.
  It is not a console NAND dump or game resource.
- test_wii_sysconf_image.cpp verifies original-free native GuestFiles +
  IosBus read-only open, full 16 KiB guest RAM read, EOF, seek, read again,
  write denial, close, and invalid options. Optimized and ASan/UBSan passed:
  https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44655385315
- V139 extends the already-verified V92 trial-start filesystem mount with
  this synthetic config. Do not replace a mount while /dev/fs or file
  descriptors are live. The initial late-mount attempt correctly failed
  under public assertion 410; it was fixed by moving resource installation
  to the existing safe mount boundary. No guest data/registers are forced.
- wii_ios_yield_scheduler.h allows one explicitly scheduled native IOS
  service step, not ARM emulation or automatic completion/IRQ delivery.
- V140 uses native_external_irq.h to enter the installed original vector,
  with correct interrupted-guest SRR0/SRR1. It deliberately STOPS before
  original vector/handler execution.

## Priority next original-code tests

1. Resume at 0x80000500 using V140's authenticated vector and saved CPU
   state. Execute the original interrupt vector and registered handler.
2. Verify the original guest's IPC ACK, interrupt W1C, Y2 response handling,
   published queued IOS_Open reply (Y1), and scheduler/context return.
   Preserve the earlier registered deferred STM event.
3. Follow the original SC completion callback into IOS_Read of SYSCONF,
   original file parsing and a guest-authentic status transition away from 1.
4. Only after the original retry completes, advance OSInit to its next
   authentic BL target at 0x8052BE14. Never force guest r3, CR0, PC or
   the SDA SC status byte to claim progress.
5. Keep all owner binaries, game-code translations and private logs off
   public GitHub and CI artifacts. Maintain the 16 original-code native
   trials, source-only regressions and sanitizer checks.

No game main, frontend, frame or gameplay reached at V140. PR #36 stays draft.
