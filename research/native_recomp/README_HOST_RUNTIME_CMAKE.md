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
can be linked safely. The ten original-free CTest programs are compiled
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
