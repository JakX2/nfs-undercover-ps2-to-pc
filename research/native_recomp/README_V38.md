# V38: original Wii OSInit IPC buffer initialization executes natively

**Verified bounded original-code execution, not a complete Wii OS, IOS, or Windows game boot.**

V38 extends the SHA-256-pinned owner-original `OSInit` native entry beyond V37's
`0x805208A4` boundary. The original `bl` at that address invokes the complete
24-byte original Wii `__OSInitIPCBuffer` at guest `0x8052AE80`. The original
helper loads the two low-memory IPC buffer words at `0x80003130` and
`0x80003134` and writes their values to the original small-data globals at
`r13-16336` and `r13-3352`. Its original `blr` returns into `OSInit`. A new,
**explicit test-only terminal `sc; blr` boundary at `0x805208A8`** stops before
`OSExceptionInit` and the following unverified service graph.

This runs real PowerPC code via NWiiRecomp's C++20 ahead-of-time native
non-split `run_game(CPUContext&)` dispatcher, **not** Dolphin, PCSX2 or a PPC
interpreter. The private DOL assembler extracts the original call and helper
only after verifying the owner's original DOL SHA-256:

`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`

## Native verification

- **26 analyzed guest functions**, with zero interpreter fallbacks on tested
  paths. The existing original system-time, interrupt, execution-parameter,
  performance-register, HID4, speculation, FPSCR, boot-information, MEM1 and
  MEM2 arena paths are retained from V37.
- **755/755 native assertions** in six continuous direct-`OSInit` scenarios
  and direct-entry helper tests. The two IPC source pointers include zero and
  nonzero values; tests verify exact 32-bit copying, unchanged source words,
  adjacent guest-memory canaries, no unexpected register/stack/LR changes,
  original helper dispatch count, and exact stop PC.
- **202/202** original-owner SHA, code-mutation, callgraph, DOL section bounds
  and output-overwrite guards, including all six instructions of the real IPC
  initializer and the original callsite.
- **14/14** V30 runtime/emitter patch guards and **13/13** V29 prerequisite
  patch guards on a clean upstream checkout.
- Optimized GCC C++20 runner, complete ASan/UBSan runner (generated C++ built
  with `-O0 -g0` to fit available build resources), and fresh unmodified
  NWiiRecomp ZIP checkout release runner all **passed**.

## Reproduce

Unzip the source-only package into one working directory. Supply an isolated
`NWiiRecomp-master` source checkout and the private owner Wii DOL:

```bash
bash run_osinit_ipc_v38.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V38_SANITIZE=1 bash run_osinit_ipc_v38.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner applies only existing independently written V15/V26/V29/V30
patches, creates temporary game-derived files under `mktemp -d` and deletes
those files on exit. The submitted scripts, C++ tests and documentation contain
no proprietary game instruction bodies, executable, assets, or generated game
C++. They must remain out of GitHub and any distributable ZIP.

## Limits and next work

Original `__OSInitIPCBuffer` is just a **copy of two pointer words**. This
milestone does **not** initialize IOS IPC communications, validate physical IPC
buffer ranges, or implement the subsequent `OSExceptionInit` at `0x80520BF4`.

This test enters original `OSInit` at `0x80520670` directly; the last verified
one-piece original `__start` chain still stops at V26's `0x805206B4`. Five
V26 harness sources also remain unpublished, a separate reproducibility gap.
Do not claim native Windows boot, `main`, first frame, frontend or gameplay.
The next bounded native step is original exception/system-call initialization
and later OS/IOS services, but joining V27–V38 into the continuous `__start`
path remains a high priority. Preserve draft PR #36 and parallel Carbon work.
