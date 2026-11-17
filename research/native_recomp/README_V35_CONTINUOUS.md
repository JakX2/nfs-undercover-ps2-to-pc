# V35 candidate: genuine continuous Wii __start enters OSExceptionInit prologue

Status: owner-original V35 continuous native CI is not yet verified.
The existing owner-original DIRECT-ENTRY V39 OSInit→OSExceptionInit
research validates a related but independent execution path.

## Original PowerPC execution boundary

The verified continuous Wii startup enters genuine original __start at
0x8000403C and has passed V26 through V34. V35 restores the original
OSInit branch at 0x805208A8 to OSExceptionInit at 0x80520BF4 after the
successful native IPC-buffer helper. This original function constructs its
64-byte guest frame, saves the original return LR 0x805208AC, and calls
the genuine _savegpr_20 helper again.

The new source-only private fixture extracts the owner's authentic
180-byte Wii exception prefix 0x80520BF4..0x80520CA4 and original text
literal at 0x80520F28 from the SHA-256-pinned Wii DOL. The minimal test
runtime explicitly seeds that literal into its guest memory because
it does not load the full text image into guest MMU memory yet.

Sixteen owner-original native trials select the documented original fast
branch with low-memory flag at 0x80000060 nonzero. The test verifies:
- Guest exception entry, nested original _savegpr_20 and exact ABI LR.
- New 64-byte exception frame within the previous OSInit stack frame.
- Original source-literal LWZU, template arithmetic and register effects.
- No writes to exception-vector memory before the explicit stop.
- Complete previous V26–V34 hardware, time, interrupts, BSS, MEM1/2,
  IPC-buffer and register-state regression invariants.
- Zero interpreter fallback, no fake original exception logic.

The **explicit test-only terminal syscall is at 0x80520CA8**, before
the per-vector installation loop. Since the synthetic sc would otherwise
fall through into the following BLR after is_running is cleared, the
V35 C++ test throws an intentional exception at that exact guest PC to
prevent a false stop claim.

The alternative zero-valued 0x80000060 path is explicitly guarded at
0x80520C44 before the unimplemented original DBPrintf call, and
conservatively inferred address-operand roots are guarded by test-only
syscalls; these guards are not claimed as executed original services.
The authentic __OSInitSystemCall at 0x805208AC is not executed.

## Reproduction and limits

The runner creates original-game-derived DOL slices and generated C++
only on a private GitHub Actions runner; all original Wii game instructions,
derived code, symbols, literal data and raw logs are never published.
All source patches are original-free and fail closed on changed original
DOL SHA, mismatched call graph, unsafe segment geometry and overwritten
test-output paths.

After the existing V26–V34 suite prepares an isolated NWiiRecomp
checkout:

    bash run_v35_continuous_exception.sh /private/NWiiRecomp /private/NfsMWRelease.dol

GitHub Actions must first establish the verified V34 guest-PC baseline
and then independently require native stage=35, exact stop 0x80520CA8.
No complete exception vector setup, real IOS communication, OSInit return,
native Windows game main, first frame, frontend or gameplay is implied.
