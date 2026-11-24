# Native Wii host runtime CMake build

This builds only original-free C++20 host code for Broadway IPC, Hollywood IRQ,
IOS/STM, the guest filesystem, SYSCONF and authentic IRQ/ACK/reply routing.
No original Wii game executable, generated game C++, NAND dump or assets
are needed or packaged.

Windows (Visual Studio 2022):

```powershell
cmake -S research/native_recomp -B build/wii-host -G "Visual Studio 17 2022" -A x64 -DBUILD_TESTING=ON
cmake --build build/wii-host --config Debug --parallel 2
ctest --test-dir build/wii-host -C Debug --output-on-failure
```

Linux:

```sh
cmake -S research/native_recomp -B build/wii-host -DCMAKE_BUILD_TYPE=Debug
cmake --build build/wii-host --parallel 2
ctest --test-dir build/wii-host --output-on-failure
```

The `undercover_wii_host_runtime` target is a header-only interface library.
Link it into a future Windows host executable when the translated Wii AOT
can be linked safely. The thirteen original-free CTest programs are compiled
with strict warnings, including MSVC `/W4 /WX`.
The owner-private Wii AOT harness and all authenticated NAND gates remain
independent of this build.

## V417: opt-in native IOS transport for the complete runtime

`WiiPhysicalRam` binds non-owning spans to the host MMU's physical MEM1
and MEM2 storage, excluding the eight bytes of read padding in each upstream
allocation. It rejects aliases, MMIO, cross-region spans, overflow and
addresses beyond the actual backing storage. Callers must validate a full
multi-byte range before using the existing `IosMemory` word operations.

`NativeIosTransport` owns the verified native IOS bus and scheduler for one
CPU/MMU lifetime. It accepts only the supported aligned mailbox/Hollywood
registers at physical, cached and uncached addresses. Unaligned and subword
accesses to owned registers must not fall through to legacy IOS.
The host supplies its existing atomic PI cause and mask registers; only the
Hollywood bit is published by this transport. Other device cause bits
remain intact. A PI-side clear cannot suppress a still-asserted Hollywood
source when the adapter next synchronizes. All transport operations must
run on the Broadway CPU thread; the supplied RAM and PI references must
outlive the adapter.

MMIO writes never pump IOS. The runtime must explicitly call
`service_at_guest_boundary(msr)` at an authenticated scheduling boundary.
The current conservative scheduler will defer service while an enabled
PI interrupt is pending. IRQ entry remains the caller's responsibility.
The tests cover MEM1/MEM2, invalid virtual request pointers, preserved
negative IOS results, ACK/reply separation, two distinct W1Cs, live mask
changes, and preservation of other PI bits.

This is an independent, opt-in adapter, not yet installed in the generated
NWiiRuntime executable. The existing original-game harness and legacy
runtime are unchanged except for the source-only extraction of the existing
`IosMemory` interface into its own header. Local strict C++20 ASan/UBSan
tests passed against the exact existing IOS implementation; Windows and
Linux CMake CI are the next independent verification.

## V418: opt-in NWiiRuntime MMIO binding

V417's two new native transport tests passed on both MSVC Windows x64 and
GCC Linux in [run 45303938572](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45303938572)
(10/10 on each platform). V418 adds a scoped thread-local binding, and a
reversible source-only patch to the pinned NWiiRuntime MMIO wrappers:

```sh
python3 research/native_recomp/apply_native_ios_mmio_v418.py /path/to/disposable/NWiiRecomp
```

This stages the independently implemented host headers, extends the existing
Hollywood mirror aperture, and routes supported 32-bit IPC/Hollywood accesses
to the native transport only when an explicit binding exists. Unsupported
words and 16-bit accesses within the selected IPC windows fail closed while
bound; they cannot fall back to synchronous legacy IOS. The original host PI
register implementation retains its own cause/mask and non-IPC sources. The
binding refreshes the native Hollywood level before PI reads and after PI
writes. The upstream byte-read and byte-write MMU policies are not replaced.

The binding must live on the CPU thread, with the underlying transport
and MMU allocations stable. It does not install itself at launch or
automatically pump IOS. It must not be removed in the middle of an
outstanding request/interrupt. The caller must select an authenticated
guest scheduling boundary and own IRQ entry policy. Direct legacy IOS/HLE
calls and the upstream interrupt dispatcher are not yet integrated.

Local strict C++20 ASan/UBSan binding and three Python source-seam tests
passed. The new independent CI job compiles the actual pinned upstream
MMU wrappers, IPC register implementation, PI implementation and MMIO
dispatcher, then exercises synthetic native IOS requests without a game
DOL. [V418 run 45304722483](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45304722483)
passed all three jobs, including 11/11 CTest programs on Windows and Linux,
and the actual pinned NWiiRuntime MMIO transport test. The whole-image
link lane is not changed by this patch; enabling the binding in genuine
game execution still requires an authenticated dispatch boundary.

## V421: strict access-width and original-address checks

The pinned MMU previously widened byte reads into word reads, ignored byte
writes in hardware space and treated several integer/floating-point wide
accesses as unmapped RAM. It also normalized away the original alias before
the V418 wrapper saw it. The new opt-in patch validates accesses at the
entry to all twelve guest MMU read/write methods, before normalization,
watch callbacks, widening or memory access.

```sh
python3 research/native_recomp/apply_native_ios_mmio_v418.py /path/to/disposable/NWiiRecomp
python3 research/native_recomp/apply_native_ios_width_v421.py /path/to/disposable/NWiiRecomp
```

When the native binding is active, both IPC register windows accept only
aligned 32-bit integer accesses through the supported physical/cached/
uncached aliases. Partial, floating-point, 64-bit, unaligned,
cross-aperture and unsupported alias accesses fail closed. Unknown aligned
words are still rejected by the V418 wrapper. Inactive binding and
non-IPC RAM/GX accesses retain existing behavior. This is a conservative
native IOS ownership contract, not a claim about the hardware behavior
of undocumented widths.

The direct binding tests passed under strict C++20 ASan/UBSan and the
source patch passed three original-free geometry/idempotence tests.
The pinned MMU test now runs the V418 baseline first, then independently
rebuilds with V421 and verifies unsupported widths, alias rejection and
ordinary MEM1/MEM2 accesses. Complete pinned integration results are
pending. The full-image runtime remains opt-in.

## V422: native scheduling and authentic external exception entry

The reusable `service_native_ios_boundary` bridge combines one permitted
IOS scheduler step with the existing native PowerPC external IRQ entry.
It rejects uncertified, stopped, unmapped, unaligned or unsupported guest
contexts and defers host callbacks, pending HLE reschedules and in-flight
context dispatch. A pending unrelated PI source remains the responsibility
of the existing runtime and prevents another IOS service step. An enabled
Hollywood source with EE disabled remains latched; with EE enabled, the
bridge requires mapped, byte-verified vector contents before changing
PC, MSR, SRR0 and SRR1. It neither acknowledges the hardware nor executes
the vector or a guest return.

The caller must provide an independently authenticated original vector,
certify that the PC is the next not-yet-executed guest instruction and
account for guest-side nested interrupt handlers. On NativeEntered the
caller must redispatch the changed PC; NativeMasked must not be sent to
the legacy IOS dispatcher. The helper is deliberately not automatically
called by upstream process_pending_callbacks. Full runtime scheduler
integration needs a verified AOT boundary and original vector emission.

Original-free strict C++20 sanitizer tests passed the deferred ACK,
separate Y2/Y1 entry, vector mismatch rejection, preserved register state
and unrelated PI ownership. The pinned CPU/MMU test now includes the same
boundary bridge using a synthetic vector and explicit synthetic return.
[V422 run 45306524682](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45306524682) passed 12/12 CTest programs on Windows and Linux and the pinned CPU/MMU integration.

## V423: exclusive AOT IOS dispatch session

A scoped `NativeIosAotSession` binds the V422 transport to one CPU and
allows polling only at explicitly certified dispatch boundaries. It
rejects other enabled PI sources, legacy callbacks, expired decrementer,
vblank and outstanding host context dispatch rather than hiding them.
It tracks an in-flight external interrupt and requires a matching
certified saved PC/MSR before admitting another service step. This is
a bounded exclusive experiment, not a general Wii event dispatcher:
it does not support nested interrupts or guest-selected alternative
contexts, and matching PC/MSR alone is not proof of RFI.

The original-free program in `wii_v423_synthetic_program.h` constructs
PowerPC words independently. It submits a native IOS Open request using
guest MMIO writes, enables EE with mtmsr, and executes a low-memory
handler which reads the live Y bits, acknowledges both mailbox and
Hollywood registers, restores its scratch GPR through SPRG0 and uses
rfi. The test harness requires two handler bodies and two certified
resumes, then executes the next guest instruction exactly once.
It checks both positive and negative IOS replies, preserved unrelated
PI bits, and zero legacy IOS calls or interpreter fallback. The runner
uses the real pinned NWiiRecomp Analyzer and both C++ emission modes
with the already tested V15/V26/V63/V74/SPRG patches and real MMIO wrappers.

The standalone session test passed strict C++20 ASan/UBSan locally; the
synthetic encoding checks passed. Actual generated split and non-split
execution is pending CI. No original game data or generated C++ is
committed. The full original-game runtime remains unchanged and opt-in.
