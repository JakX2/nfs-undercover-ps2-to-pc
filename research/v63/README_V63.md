# V63: pinned public Carbon resource-loader source and PE32 address preflight

**Read-only, offline, no executable patch, no ASI installation, no original
Carbon executable or proprietary game assets in GitHub.**

## Why this is the next integration lead

The [XNFSModFiles public research project](https://github.com/xan1242/xnfsmodfiles)
describes loading additional chunk resource files for several Black Box
Need for Speed titles, including **Carbon PC**. This is useful evidence that
a *resource-file loading pathway* may be a practical future experiment.

This does **not** prove that an Undercover Wii scene can be placed in the
native Carbon PC world system, or that a borrowed scenery ROOT has valid
materials, streaming table ownership, visibility, collision or navigation.

### Pinning the upstream evidence

All addresses below are derived from the public project at Git commit
`de4164ac55620f38a173ddf855c28bd036e74883` (2017-09-30):

- [Carbon_addresses.h at pinned commit](https://github.com/xan1242/xnfsmodfiles/blob/de4164ac55620f38a173ddf855c28bd036e74883/XNFSModFiles/Carbon_addresses.h),
  Git blob `0720a4ccc79d5ffc132bb179322fc1554a394024`.
- [dllmain.cpp at pinned commit](https://github.com/xan1242/xnfsmodfiles/blob/de4164ac55620f38a173ddf855c28bd036e74883/XNFSModFiles/dllmain.cpp),
  Git blob `a0a9ed10724645ae5a1074ab5c971ea4d1f082fe`.
- [README at pinned commit](https://github.com/xan1242/xnfsmodfiles/blob/de4164ac55620f38a173ddf855c28bd036e74883/README.md),
  Git blob `91dbb272875f437122eeda227456ae718842a26c`.

The source describes Carbon-specific `GAME_CARBON` compilation and separate
two-stage resource loading via `CreateResourceFile` and `BeginLoading`.
Its fixed **virtual address constants** are:

| Historical loader symbol | Source-specified VA |
|---|---|
| `CreateResourceFile` | `0x006B32C0` |
| `BeginLoading` | `0x006B5910` |
| Stage-one detour entry | `0x006B6D56` |
| Stage-two call entry | `0x006B7850` |

These addresses are **claims of the 2017 plugin**, not independent executable
disassembly or confirmation of your game edition. The loader detours
historical code locations, and the source parses configuration with an
unbounded `%s` field. Its inline-comment copying logic also warrants
independent safety review. **Do not install or run this old plugin unchanged
merely as an exploratory test.**

## V63 new read-only executable preflight

`v63_carbon_runtime_preflight.py` accepts a locally owned original `NFSC.exe`
and checks, without modifying or executing it:

- The MZ / PE32 x86 file headers, 32-bit image base, image size and section
  table; malformed files fail closed.
- Whether each of the four *historical loader virtual addresses* maps to
  one file-backed, executable PE section.
- SHA-256 of the exact opened file before/after analysis, optional trusted
  expected SHA-256 guard, and file metadata/path identity to catch many
  concurrent changes.
- Exclusively writes a new **metadata-only** JSON report. No executable bytes,
  local input paths, patches, loader code, models or game assets are exported.

Example Windows PowerShell command using *your own original executable*:

```powershell
py -3 research/v63/v63_carbon_runtime_preflight.py `
  --executable "D:\Games\Carbon\NFSC.exe" `
  --expected-sha256 "64_HEX_DIGIT_TRUSTED_EXE_SHA256" `
  --report "D:\PrivateResearch\carbon_exe_v63_preflight.json"
```

All paths are examples. A SHA-256 guard verifies file bytes, **not** game
provenance or authorization. The tool checks addresses and file section
mapping, **not** matching assembly, instruction boundaries, calling
conventions, active rendering code, safe hook space, game version identity
or whether runtime calls are valid. Even if all four addresses map neatly,
`safe_to_install_or_patch` is always **false**.

## Synthetic tests

```sh
python -m unittest discover -s research/v63 -p test_v63.py -v
```

The 24 asset-free cases build toy PE32 files with executable or
nonexecutable sections, alternate image bases, virtual-only addresses,
corrupted signatures, altered source files and path replacements. They test
the preflight parser, **not the real Carbon executable**.

## What we still need before an actual game test

1. An independently verified original Carbon PC executable edition and
   related original world/master archives, inspected **privately**, without
   publishing the game files.
2. Version-specific instruction/ABI checks at loader addresses. Matching
   executable section locations alone are far from sufficient.
3. A *safe, reviewed* sandbox experiment using a known-good Carbon resource
   to establish loader behavior without altering an existing installation.
4. Separate proof of scenery registration, original Undercover geometry
   placement, shader/texture ownership, streaming index references, collision,
   navigation and in-game rendering.

The existing Wii model conversion, RedBuilding scene and V41–V62 tooling are
still **offline research**, not a playable native PC port.
