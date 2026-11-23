# Windows native IOS reply self-test

The native C++20 V374 regression checks Broadway IPC request submission,
native Starlet ACK, real Y2 and Hollywood PPC_FLAG acknowledgements,
then the queued Y1 response and its original return code. It checks that
an unsupported open retains a negative IOS result instead of being turned
into success. **It is an original-free hardware/runtime test, not a game
boot, a Wii handler round trip, or evidence of a working frontend.**

On Windows, use a **Visual Studio 2022 Developer Command Prompt** or a
terminal with **MinGW-w64 g++** available. In a clone of the repository
on `research/wii-native-recomp-preflight`, run:

```bat
research\native_recomp\windows_nand_reply_selftest.bat
```

The script compiles the independently authored test and its runtime headers
from this checkout, executes it, reports PASS or FAIL, and removes its
temporary build folder. It never reads or changes game assets or executables.

Expected final output on success:

```text
PASS: V374 authentic ACK, Y2/flag, queued Y1 and negative IOS reply
PASS: Windows native C++20 V374 deferred reply regression.
```

If it fails, retain the **compiler diagnostic or final FAIL line** and
the compiler version. Do not upload private game files or translated code.
The authenticated owner-original CI remains the authority for what
original Wii game logic actually executed.
