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
can be linked safely. The eight original-free CTest programs are compiled
with strict warnings, including MSVC `/W4 /WX`.
The owner-private Wii AOT harness and all authenticated NAND gates remain
independent of this build.
