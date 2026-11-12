# Carbon PC first-model namespace preflight (V13)

**2026-11-11 | Source-only. No retail game or ASI executed.**

The next reliable gate for our Undercover PS2/Wii → Carbon PC conversion is
determining whether a candidate model/texture pair can coexist with the model
and texture identities already indexed in the **owner's Carbon PC RB files**.

A successful PC-shaped eSolid parser readback (V10–V12) is not sufficient:
the original Carbon resource manager may already have an object under the
same 32-bit identity. A collision could load the wrong geometry or image
or act as an unintended replacement. Actual loader conflict policy is still
unknown, so the safe default is to classify these identities as **blocked**.

## New offline gate

`carbon_pc_resource_namespace_gate.py` exports
`audit_carbon_registration_namespace(candidate_geometry, candidate_textures,
native_carbon_geometry_roots, native_carbon_texture_roots)`.

All arguments are *in-memory, original-format resource-root bytes*, not
paths to a game installation. Supply complete candidate PC geometry and PC
texture roots, plus at least one independently parsed original **Carbon PC**
geometry root and one texture root from the owner's private assets.

Each root is structurally verified using the existing independent
`geometry_hash_control.parse_geometry_root` and
`texture_metadata_pixel_bridge.parse_pack` readers:

1. Every candidate eSolid hash is backed by the root's sorted model index.
2. Every eSolid's **complete** local texture table is decoded. Materials
   must resolve in either candidate PC textures or one of the supplied
   Carbon PC texture roots; face-only texture closure is not enough.
3. Candidate eSolid identities are intersected with the supplied Carbon PC
   model identities.
4. Candidate texture identities are intersected with the supplied Carbon PC
   texture identities. Even an apparent intentional override is blocked
   until an explicit, separately verified override policy exists.
5. A positive result returns
   `ELIGIBLE_FOR_OWNER_LOCAL_EXPERIMENT_NOT_RUNTIME_PROOF` and never
   `SAFE_TO_INSTALL` or `RENDERED`.

The result is **aggregate counts and booleans only**: no private model hashes,
texture hashes, debug names, geometry vertices, RGB pixels or resource bytes.
Native roots are bounded to 32 supplied geometry/texture packs per input.

**Important limitation:** this checks ONLY the supplied RB roots, not the
full Carbon PC resource registry, all RA/RB worlds, the active runtime cache,
global car/frontend IDs, texture sampling/format ABI, visibility, placement,
streaming or game-side registration. Absence of collision is not proof that
the loader can successfully register a resource.

## Integrated into the existing first-model converter

`undercover_pc_first_model_gate.verify_single_model` now optionally accepts
`native_carbon_geometry_roots` and `native_carbon_texture_roots`.
When both are provided, the converter first generates the original
Undercover model as a PC-shaped eSolid and its full-table private DXT5
candidate **in memory**, performs all its existing face/UV/material/image
readbacks, and passes those very same bytes to the namespace auditor.
The returned `carbon_pc_namespace_preflight` entry contains only
the aggregate risk report. Its default remains `None` for callers
without owner-original native Carbon PC roots, and supplying only one
reference list is rejected. The public CLI's default behavior is unchanged.

If the gate returns `BLOCKED`, no tool here renames hashes or installs
modified resources. Arbitrarily replacing resource IDs would break original
scenery-info and texture references, which also use these identities.

## Owner-local read-only CLI (no source assets published)

The existing first-model tool can now read **private extracted, complete**
Carbon PC resource-root files and pass them directly into the in-memory
comparison. They must be actual indexed PC geometry root chunks and PC
texture roots from the *same relevant installed Carbon world*, not arbitrary
files renamed to `.bin`. If all original Carbon resources haven't been
enumerated, a negative collision count does **not** establish uniqueness
across the complete game.

Example Windows PowerShell command, using fictional owner-local paths:

```powershell
python research/world_bridge/undercover_pc_first_model_gate.py `
  --undercover-ps2-tracks-zip "D:\\Private\\Undercover\\TRACKS.zip" `
  --source-section 241 `
  --pc-header-profile carbon_native_control `
  --carbon-pc-geometry-root "D:\\Private\\Carbon\\RB-GeometryRoot.bin" `
  --carbon-pc-texture-root "D:\\Private\\Carbon\\RB-TextureRoot.bin"
```

Both kinds of Carbon PC root are mandatory when either option is provided.
Each flag can be repeated for multiple owner-private roots, up to 32 per
resource category. Reads reject symlinks, missing paths, unexpectedly small
or >32 MiB files, and files that change during reading. Candidate
Undercover content and all private identities remain in memory; JSON
contains counts, blockers and explicit unverified-runtime caveats only.

**This command does not write files, modify Carbon, install an ASI,
register an asset or claim a successfully rendered scene.**

## Reproduction without copyrighted data

Run the repo's existing source-only test suite:

```sh
PYTHONPATH=research/world_bridge python -m unittest \
  research/world_bridge/test_carbon_pc_resource_namespace_gate.py \
  research/world_bridge/test_undercover_pc_first_model_gate.py -v
```

The new tests generate completely synthetic geometry and texture roots,
including known ID collisions, unresolved full-table materials, existing
Carbon texture reuse, invalid binary formats, incomplete native reference
sets, and redacted output. Additional integration tests exercise the
converter's actual candidate geometry + DXT5 output, not fabricated
resource hashes. The PR's `World bridge source-only tests` Actions
workflow runs the whole synthetic suite.

## Next decisive runtime gate

1. On the owner's Windows PC, first establish whether **one known-good,
   original Carbon PC resource bundle** can be loaded from an external,
   reversible location through the selected Carbon-compatible loader.
2. Capture Carbon-specific runtime read/registration evidence, not just a
   successful offline parser return. Preserve an untouched original install.
3. Only then attempt one source-backed **Undercover** model and its material
   using a known supported loader path and noncolliding IDs, or an explicitly
   measured override mechanism.
4. Verify the model actually renders in Carbon at a known location, with a
   before/after/restore comparison. Unconfirmed visual change remains
   `RUNTIME_NOT_PROVEN`, not a working world port.

**The Undercover world, cars, traffic, wheel physics and missions do not yet
run inside Carbon PC.** PR #35's independent Wii→native C++ physics effort is
a complementary reference, not presently wired into the Carbon executable.
