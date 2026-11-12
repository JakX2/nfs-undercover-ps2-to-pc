# V21: Source-backed Carbon PC scenery-info rebind for one Undercover model

**2026-11-12.** Research and private owner-local experiment only. No game files are modified, and original retail resources, hashes, textures and positions are not distributed.

## Milestone

V19/V20 converted one Undercover PS2 model and all of its DXT5 materials into an independently reparsed, texture-first Carbon-PC-shaped `.pcchunk` candidate. That stream had **no scenery root**. A model hash existing in the geometry resource is not sufficient to make Carbon place or display an object.

Our earlier original-file research established that Carbon PC section 141/142 scenery roots (`0x80034100`) contain six children in a stable order, including:

- `0x34102` **scenery-info table**, 72-byte records. Its empirical Carbon PC primary model hashes at offsets `+0x18` and `+0x1c` are both nonzero and equal.
- `0x34103` **scenery-instance table**, with a four-byte `0x11111111` prefix followed by 96-byte records. Each instance has a signed info-table index at `+0x54`.
- `0x3410d` auxiliary data, 32 bytes per instance.
- Additional children, placement and flags whose full runtime semantics have not been proven.

**V21 uses those source-backed offsets to replace exactly ONE referenced Carbon scenery-info entry's two model-hash fields** with the unique model identity decoded from our V20 candidate eSolid. It does not fabricate a new object, position, instance, visibility structure or unknown metadata.

## New implementation

`research/world_bridge/carbon_pc_first_model_scene_rebind.py`:

1. Independently reparses the complete V20 texture-first `.pcchunk`, including eSolid model index and complete DXT5 material-table image closure.
2. Requires the original source scenery root to match the native Carbon PC source structure and instance/link record sizes.
3. Rejects unsupported info indexes, unreferenced source rows, invalid instance indices, unaligned/truncated tables, preexisting identical target hashes and candidate collisions with other info rows.
4. Replaces only the **eight-byte window** representing the selected original PC row's two model hashes; verifies every other original byte and all instance indices remain unchanged.
5. Reparses the modified scene under the same strict native PC scene profile. All original opaque bytes, model-name fields, instance placements and auxiliary records remain untouched.
6. Reports only aggregate scene record/instance counts and explicitly marks unresolved native model references, absent post-scene control generation, runtime registration and game rendering as unverified.

### Direct original Carbon source extraction

The tool can also read the owner's **original Carbon PC** `TRACKS/L5RB.BUN` and `TRACKS/STREAML5RB.BUN` pair and select source section **141 or 142** automatically using the original 92-byte section index.

It validates bounds and 2048-byte section alignment, extracts the complete source section privately, and checks the source section's original texture, geometry, scenery, optional zero chunk and native `0x372xx` post-scene controls **before** taking a scenery root from that section. This avoids manually extracting a `.pcscene` template and rejects wrong, incomplete or mismatched native sections.

Private original source files are never written. The candidate file is never installed into Carbon.

## Owner-local commands

Run from the **PR #33 checkout**, on a system with privately owned and extracted Carbon PC originals and a V20 Undercover `.pcchunk` previously created from the owner's Undercover PS2 archive.

**Read-only structural test (default):**

```powershell
python research/world_bridge/carbon_pc_first_model_scene_rebind.py `
  --carbon-game-bun "D:\Private\Carbon\TRACKS\L5RB.BUN" `
  --carbon-game-stream "D:\Private\Carbon\TRACKS\STREAML5RB.BUN" `
  --section 141 `
  --private-candidate "D:\Private\Output\one-undercover-model.pcchunk" `
  --info-index 0
```

The `--info-index` must select an original source row actually referenced by at least one scenery instance. Index 0 is only an example, **not** a recommended or guaranteed slot for every original section. Running the tool first with no export is the safe validation path.

**Optional new private scene-root export** (not an installable bundle):

```powershell
python research/world_bridge/carbon_pc_first_model_scene_rebind.py `
  --carbon-game-bun "D:\Private\Carbon\TRACKS\L5RB.BUN" `
  --carbon-game-stream "D:\Private\Carbon\TRACKS\STREAML5RB.BUN" `
  --section 141 `
  --private-candidate "D:\Private\Output\one-undercover-model.pcchunk" `
  --info-index 0 `
  --private-scene-output "D:\Private\Output\one-undercover-scene.pcscene" `
  --write-private
```

The output must be a **NEW** `.pcscene` filename in an existing directory **outside any TRACKS directory**. The exporter independently reparses the patch, writes by exclusive creation without overwriting old files, fsyncs and verifies the new file from disk. It refuses symlinked destinations or wrong extensions. It is not a Carbon `.BUN`, and the user should never rename it or place it inside the installed game. Nothing about this path validates the third-party external loader.

Alternatively, for an already privately extracted native `.pcscene` root, use `--carbon-pc-scene-root <path.pcscene>` instead of the original bundle/stream arguments. The same read-only and optional export controls apply.

## What is still missing

- **Remaining scenery model references.** A real section 141/142 native Carbon scene has multiple scenery-info rows. V21 deliberately preserves them. The converted candidate only supplies ONE Undercover model; other original Carbon model references are not resolved by this two-root candidate. A complete sector must preserve/link its existing Carbon model registry correctly.
- **Native stream control and resource registration.** The `0x372xx` post-scene records are verified in the original Carbon control, not regenerated or transplanted. No model registration or stream index relocation has been demonstrated.
- **Actual visibility, collision and render behavior.** The original instance matrix, placement and flags are retained byte-for-byte, but there is no tested result from the running Carbon engine and no proof that the selected source row is visible at the player's camera.
- **Windows loader ABI.** A parser-valid `.pcchunk` plus a parser-valid `.pcscene` is not a registered, working Carbon external `.BUN`. The native XNFSModFiles loader needs its own original-resource positive control.

The next meaningful step is checking a **source-backed Carbon scene/model reference closure** across the edited native scenery root, the preserved original native Carbon geometry roots and the one converted model. A later full stream-sector builder would also need native `0x372xx` control semantics, correct placement and actual runtime evidence.

## Regression validation

`test_carbon_pc_first_model_scene_rebind.py` uses entirely synthetic native PC scenery roots, original-style section 141/142 indices, source section envelopes and V20 geometry/DXT5 candidate resources. It covers exact two-hash-field changes, instance links and auxiliary data preservation, selection of referenced rows, duplicated/colliding model identities, invalid geometry/texture material closure, corrupt source framing, source index bounds, private file immutability, explicit opt-in export, no overwrite, wrong paths and symlinks.

**1,837 source-only tests passed** in [GitHub Actions 43257937878](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/43257937878) on code/test commit `f3ca71e1`. Documentation-only head changes should have their own CI checked separately.

**Project status:** Experimental V21 native PC scene linkage exists. Undercover content has **not** been proven rendered inside Carbon PC, and no playable port exists. PR #33 remains draft, `main` unchanged, Wii-native decompilation PR #35 separate.
