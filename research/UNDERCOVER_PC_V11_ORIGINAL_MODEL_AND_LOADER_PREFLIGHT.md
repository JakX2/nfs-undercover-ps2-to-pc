# V11 · Original Undercover PS2 first-model geometry and Carbon external-loader preflight

**2026-11-05. Read-only owner-original investigation. Not a Carbon PC in-game model load, not a playable Undercover port.** All original models, pixels, resource hashes, coordinates and candidate game-resource bytes remain private.

## Original-source geometry result

An independent bounded PS2 VIF decoder examined the owner's CRC-verified original two-member Undercover PS2 RB archive. The original scenery/index survey selected two small **image-backed**, scene-referenced source eSolids in section **241**, both in original geometry pack **0**.

| Source model ordinal (zero-based) | 6 | 42 |
| --- | ---: | ---: |
| Original triangle faces | **8** | **144** |
| Original PS2 VIF strips decoded | 1 | 11 |
| Original position/UV vertex samples | 14 | 288 |
| Distinct used source material identities with valid source image indexes | 1 | 1 |
| Maximum decoded source bounding-box discrepancy, original units | 0.0100 | 0.0138 |
| Independent **in-memory PC-shaped eSolid** root byte length | **1,236** | **11,920** |
| PC-layout XYZ + UV + material + oriented face multiset matches original | **Pass** | **Pass** |
| Carbon PC engine resource registration | **Not tested** | **Not tested** |

The original-source mirror constructs native-style `0x80134000` geometry roots, indexed model/eSolid children, 144-byte PC mesh records, 16-bit triangle indexes, and 36-byte XYZ/normal/UV vertex data. A second readback confirms all 8 and 144 original faces and their texture-local labels and UV corners, using exact f32 serialization. The byte counts above belong to this independent *offline mirror*, not necessarily to the separate repository converter. No candidate bundle was installed or distributed.

## Source-only V11 tool and tests

Draft [PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33) now includes `undercover_pc_first_model_private_obj_preview.py`, which performs the repository's full V10 single-model PC geometry/DXT5 validation and then generates a standard Wavefront OBJ **from the native PC parser readback**, not straight from unverified PS2 bytes. No game files are written by default; optional owner-local OBJ export requires an explicit destination and opt-in, refuses existing files/symlinked paths, and rejects output inside extracted game directories. The source-only downloadable V11 kit includes an offline, network-free 3D OBJ viewer.

The full V11 owner-original conversion **using the new GitHub tool** has not yet been executed against original source in this milestone. The independent local VIF/PC-shaped mesh proof above is narrower: geometry and material-index identity, not a verified native PC DXT5 resource registration/renderer.

GitHub Actions clean-checkout source-only suite: **1,604 / 1,604 synthetic tests passed**. V11 adds 30 source-free OBJ/ownership tests and 14 additional Carbon PE/address preflight tests. Offline viewer syntax and file-input behavior were checked in Node and headless Chromium with an original-free synthetic OBJ.

## Alternative runtime path: source-backed external bundle loader

Public third-party project [XNFSModFiles](https://github.com/xan1242/xnfsmodfiles) advertises a **Carbon** ASI build and contains C++ calls to `CreateResourceFile` and `BeginLoading` to load additional resource bundle files at pre-initialization or post-initialization stages. Its sample configuration includes `0,1,MODS\FileToBeLoadedAtPreinit.bun` and `1,1,MODS\FileToBeLoadedAtPostinit.bun`. This is a *potential* route around modifying complete world streams. A generic resource loader does **not** establish Carbon streaming section, scenery-info, texture-sampler or collision registration.

A separate **read-only** `carbon_pc_external_loader_abi_preflight.py` was run on the owner's original `NFSC.exe` in a private environment, using the five absolute Carbon addresses declared in the third-party source. All five resolve uniquely into nonzero executable PE32/x86 code; the entire executable SHA-256 matched the previously audited original: `baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3`. This confirms **static address placement in this exact binary**, not that the ASI hook works, is safe, handles different Carbon versions, or can register/render new world models. No code injection, file modification or third-party binary installation was performed.

Source references:
- [XNFSModFiles README](https://github.com/xan1242/xnfsmodfiles/blob/master/README.md)
- [XNFSModFiles Carbon address definitions](https://github.com/xan1242/xnfsmodfiles/blob/master/XNFSModFiles/Carbon_addresses.h)
- [XNFSModFiles resource load implementation](https://github.com/xan1242/xnfsmodfiles/blob/master/XNFSModFiles/dllmain.cpp)

## State and next experiment

The earlier owner Windows V7 private texture replacement was accepted offline; Carbon launched with the staged stream and subsequently returned to a verified original state. The altered image was **not visually proven** and the exact-image-span Process Monitor test remains deferred. No Undercover scenery has rendered within Carbon PC.

**Next falsifiable loader experiment:** establish the unmodified Carbon runtime loads a **known-good, owner-original Carbon resource** from a separate reversible bundle before attempting any new-identity Undercover model, texture, scenery or visibility registration. Require explicit owner approval, private backups and a clean undo path for all external ASI/runtime experiments. Never overwrite original game assets or distribute extracted model/texture bytes.

**The 144-triangle original model has been decoded and converted to a structurally checked PC-shaped mesh offline, not integrated into Carbon.**
