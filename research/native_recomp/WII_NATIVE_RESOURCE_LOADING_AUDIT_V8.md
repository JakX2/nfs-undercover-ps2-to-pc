# V8: Original Undercover Wii resource-loading bridge (2026-11-13)

**Scope:** owner-original resource inventory, code-anchored host path resolution and DVDOpen HLE patch. No new runnable game build.

## Findings

The owner's ELF contains embedded disc paths `NFS\\ZDIR.BIN`, `GLOBAL\\GAMEPLAY.BIN`, `FRONTEND\\FRONTB1.BUN`, `FRONTEND\\FRONTB1.LZC`, `TRACKS\\STREAM%s.BUN` and more.

The uploaded real archives were inspected without decompressing or redistributing their contents:

| Archive | Files | Bytes unpacked |
|---|---:|---:|
| GLOBAL.7z | 44 | 30,991,268 |
| FRONTEND.7z | 7 | 23,165,063 |
| CREDITS.zip | 22 | 721,288 |
| MEMCARD.zip | 11 | 74,110 |
| MOVIES.zip | 10 | 121,351,792 |
| **Inspected total** | **94** | **176,303,521** |

Five representative resource names from these categories were confirmed present. `NFS/ZDIR.BIN` was not in the five archives checked, and may be elsewhere in the original disc. `GLOBAL/GAMEPLAY.BIN` and `GLOBAL/ATTRIBUTES.BIN` begin with `VPAK`; `GLOBAL/GAMEPLAY.LZC` and `FRONTEND/FRONTB1.LZC` begin with `JDLZ`. Those signatures suggest separate container/decompression work after path resolution.

## Port-side fix

The stock NWiiRuntime `DVDOpen` helper appends a Wii filename directly to the host `game_dir`; Wii backslashes and mixed case can fail on Unix. The opt-in V8 helper resolves Wii-style paths under a standard `files/` tree, a flattened host tree, or the owner's `ExtractGLOBAL`-style directories. It rejects traversal, host absolute paths, symlinks and ambiguities. The DVDOpen patch also bounds guest string scanning to 4096 bytes.

**Validated:** 26 original-free C++ path tests, 8 original-free Python archive-audit assertions, clean and idempotent patch application against the upstream NWiiRuntime DVD helper, and GCC 14.2 C++20 syntax validation of the patched DVD helper.

## Limitations and next step

The uploaded ZIP/7z archives are not mounted by NWiiRuntime; resources must be unpacked to ordinary host files before real game execution. The existing VirtualDisc low-level file reader expects `sys/boot.bin`, `sys/fst.bin` and `files/`; those disc-layout files were not present in the checked Drive folders. Correct Wii FST/DI operation, async callbacks, JDLZ/VPAK decoding and the original ZDIR resource index still need investigation. No executable was linked or booted during V8. All original game binaries and payload bytes remain private.
