# Native PC port feasibility and engineering gates

**2026-11-11.** This plan distinguishes a native port of the **Wii/PS2
Undercover release** from Dolphin/PCSX2 emulation, the different existing
retail PC Undercover release, and offline Carbon PC experiments in PR #33.

## Is it possible?

**Technically yes, through independent engine reconstruction.** The Wii
PowerPC executable cannot be linked unchanged into a Windows x86-64
executable. Wii is big-endian PowerPC (Broadway) with a console-specific
graphics/input/runtime ABI. PS2 uses Emotion Engine MIPS plus vector units
and different hardware services. A Windows native port requires C++ host
reimplementations of game engine and platform interfaces (or a substantial
binary-translation and compatibility layer, which is not the path being
implemented here).

The owner-provided Wii executable preserves **27,941 sized named PPC
function symbols**. They greatly assist reconstruction, but symbol names
are NOT recovered game source. Wii is the primary logic oracle and PS2
MIPS the secondary reference. Proprietary game data remains owner-local.

## Staged milestones

| Gate | Acceptance evidence | Actual status |
|---|---|---|
| 0: Host-native C++ physics | Windows/MSVC and Linux CMake builds; synthetic 2- and 4-frame smoke tests | **PASS (V21)** |
| 1: Real Wii differential | Same pre/post body state under original Wii runtime and host, including numerical tolerances | NOT DONE |
| 2: Vehicle handling/contact | Verified wheels, suspension, steering, collision and contact solver | NOT DONE |
| 3: Asset streaming | Native runtime reads owner-local original meshes, textures, stream IDs and LOD | PARTIAL offline format research, **no native runtime loader** |
| 4: PC presentation/runtime | Window, input, renderer, audio, camera and main-loop integration | NOT DONE |
| 5: First driveable road | Original road/car loaded on PC, player can drive and collide without emulator | NOT DONE |
| 6: Complete game | UI, race events, AI/traffic, world streaming, saves, script/progression and packaging | NOT DONE |

A passing synthetic test is NOT a measured percentage of the game's
total decompilation. This repo currently demonstrates a source-only native
host physics program, **not** the game running on PC.

## Next technical priorities

1. Define an owner-local **Dolphin original-runtime trace contract**:
   body/state addresses, timestep, flags, and pre/post velocity, force,
   torque, quaternion, transforms, plus known vtable identities.
   Keep game binaries and original assets private.
2. Differentially test the V7–V20 reconstructed physics under identical
   inputs. Triage PPC FPSCR/rsqrt rounding and source callback mismatch.
3. Recover Primitive::Prepare, UpdateCollider, DoWorldCollisions,
   vehicle-specific dynamic vtables, steering, tires and suspension.
4. Put a stable native scene/physics API on top of the current bounded
   big-endian Wii memory decoder instead of exposing 32-bit Wii pointers
   directly to PC gameplay.
5. Continue owner-local asset/stream reconstruction, informed by
   geometry/texture identity work in PR #33.
6. Build the native renderer/input + static road collision test only
   after one controlled car/road physics trace matches the Wii.

## Current branches and verified PC milestone

- **Draft PR #35:** PPC physics/Attrib research and V21 native physics host.
  `research/wii_executable/CMakeLists.txt` compiles
  `nfsuc_wii_physics` static library and the
  `nfsuc_physics_smoke` CLI on Windows and Linux. A tested workflow
  runs both synthetic scenarios and uploads time-limited original-free
  binaries. This is the first actual native Windows target, not a
  playable build.
- **Draft PR #33:** PS2 ↔ Carbon native-format scenery experiments,
  offline model/texture results and no proven native Undercover load.
- **Draft PR #34:** stripped PS2 MIPS ELF call-site indexing.

Only independently authored code, tests and aggregate research findings
belong in GitHub. Any eventual runtime should load legitimate
user-supplied original game data, not ship copyrighted assets.

**Conclusion:** a native Wii/PS2 Undercover PC port is possible in
principle. V21 proves selected recreated physics components compile and
run natively on Windows. Complete gameplay still requires substantial
engine, renderer, asset and runtime work, plus original-Wii validation.
