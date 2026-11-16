# V65: Original Wii EXIInit three-channel transfer-control polling prefix executes natively

**Status:** isolated bounded owner-original Wii PowerPC native execution, *not* integrated continuous `OSInit`, full EXI service, or a bootable Windows port.

The original `EXIInit` at `0x804EF9BC` begins by testing the low bit of the Wii External Interface channel control registers at `0xCD00680C`, `0xCD006820`, and `0xCD006834`. On a busy indication from any channel, the original PowerPC conditional branch returns to the first channel. Using the owner's independently SHA-pinned Wii DOL, this harness extracts the **unaltered first 22 PowerPC instructions** into a private test DOL, translates them through unmodified NWiiRecomp and exercises the resulting C++ with **zero interpreter fallback**.

The only synthetic guest instructions are a test-only syscall and return at `0x804EFA14`, replacing the first untested original `__OSMaskInterrupts` call and following instruction. The test stops before that call. It does *not* execute `__OSMaskInterrupts`, EXI handler registration, device identification, EXI DMA, or other hardware services.

## Verified semantics

- **260/260 native assertions**, over ten explicit ready/busy status schedules and one intentionally permanently busy test device. All three original MMIO addresses and read order are checked against an independent oracle. The never-ready case is bounded by an eight-read budget and cannot silently complete.
- **115/115 fail-closed checks** reject single-byte mutations of each private original/synthetic instruction, malformed DOL segments/entry point, truncated or appended private images, owner SHA mismatch, and nonempty output directories.
- Full **optimized C++20**, **ASan/UBSan**, and **freshly extracted unmodified NWiiRecomp archive** runs passed; the clean source required only the original-free V15 dispatcher and V26 syscall-PC patches.
- The analyzer recognizes 2 code entries including the synthetic test stop; these are not two independent original game functions.
- **Limitations:** MMIO read values are supplied by the test, and the runtime does not emulate EXI transfer completion or timing. EXIInit is entered directly, not from `OSInit` at `0x805208C4`. The V64 longer direct `OSInit` path separately reaches `0x805208C4` but is not yet bridged. The genuine `__start` path remains at its V26 checkpoint.

Reproduce privately with an owner-original DOL matching SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`:

```bash
bash run_exi_poll_v65.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V65_SANITIZE=1 bash run_exi_poll_v65.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The temporary private DOL, emitted original game C++ and compiled native executable are removed when the runner exits. Source-only distribution includes **no game executable, original PPC function bytes, game assets, generated game-code translations or proprietary tooling**.

**Next priority:** integrate the verified EXI ready-poll prefix into the original `OSInit` call at `0x805208C4`, then extend through `__OSMaskInterrupts` and EXI handler registration using explicit MMIO and peripheral models. Do not claim `main`, first frame, frontend or gameplay before verified.
