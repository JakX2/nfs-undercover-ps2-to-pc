# NFS Undercover Wii/PS2 → Carbon PC: native scenery identity bridge V27

**STATUS: Research-only offline file-format proof. Not installable.** Nothing in this package has been tested in a running Carbon PC game. Do not copy `.chunk` or `.tpk_payload` files into the game. There are no completed world-stream, collision, navigation, placement-sector or shader integration steps.

## What's genuinely new in V27

Previous releases could put Undercover Wii's RedBuilding geometry and texture hash inside the native PC mesh layout, but they **borrowed** the existing Carbon lamp identity `AXOU_PARKLAMPA_1B_00`. V27 adds the original Undercover scenery as an **additional named object** in an isolated Carbon PC geometry container, **without replacing the original Carbon object**.

- The world geometry outer container is `0x80134000`.
- Its `0x80134001` catalogue contains `0x134002` (catalogue descriptor) and `0x134003` (sorted array of 8-byte `(object hash, zero)` records), plus an unchanged `0x80134008` empty record in the tested sample.
- Each `0x80134010` scenery component holds a `0x134011` header containing the **same object hash**, its string name and transform/bounds.
- The scene count in this catalogue's `0x134002` payload `+0x0C` tracks the number of components in **this** binary chunk. The field at `+0x08` is not modified; its meaning is not established. The 29-component sample's count goes **29 → 30**.
- The identity hash used by all three Undercover Wii RedBuilding components is the Black Box BIN hash, initialized to `0xFFFFFFFF`, with `h = (33*h + next ASCII byte) & 0xFFFFFFFF`. The original source data supplies `XBU_REDBUILDING_1B_00 → 0x80B4A527`, 1C `0x80B53188`, and 1Z `0x80C1CE3F`.
- The new object is inserted in ascending ID order in both the directory and the component list; parent and child sizes are rebuilt; the old components are **byte-for-byte identical** after re-reading.
- The new object's `0x134011` name is the authentic Wii name and its ID is the authentic Wii ID. Its mesh retains **400 PC-format vertices, 260 faces**, repaired bounds and original texture hash `0x2CAB30BD` from V26. The material/shader implementation is **still borrowed**, and no actual Carbon runtime has rendered it.

### Offline insertion report

| Attribute | Before (original Carbon PC sample) | After (V27 sample) |
|---|---:|---:|
| Carbon scenery objects preserved | 29 | 29, byte-identical |
| Undercover scenery objects added | 0 | 1 |
| `0x134003` directory entries | 29 | 30, sorted |
| Source RedBuilding identity | Missing | `0x80B4A527` |
| Added mesh vertices and faces | Missing | 400 / 260 |
| Other component payloads | Original | Unchanged |

### Full game-stream ID collision audit

I performed a **read-only** scan of the user's actual **1,238,368,256-byte** Carbon PC `STREAML5RA.BUN`:

- 5,009 `0x80134000` geometry containers, 5,009 recognized catalogues, **zero catalogue-format anomalies**.
- 40,809 indexed scenery-ID occurrences, containing **32,818 distinct IDs**. Some IDs intentionally repeat across different containers (3,023 IDs occur in more than one), so **do not require global uniqueness** for original Carbon IDs.
- `0x80B4A527` **does not occur** in the original PC world's indexed geometry directories. That only checks this particular stream; it is **not** a guarantee of collision-free integration into other game systems.

The `audit_identity_v27.py` source also cross-checks extracted original named components:

| Original reference set | Decoded headers | Stored ID equals computed BIN hash |
|---|---:|---:|
| Carbon PC | 198 | **175** |
| Carbon Wii | 69 | **69** |
| Carbon PS2 | 69 | **65** |
| Undercover Wii RedBuilding | 3 | **3** |

All 65 named matched Carbon PC/Wii components share the **same stored ID**. All 69 named matched Carbon PC/PS2 components also share the same stored ID. The **23 PC noncanonical IDs** and **four PS2 noncanonical IDs** matter: the writer preserves them as found and **never recalculates original Carbon IDs** just because their displayed names hash differently.

## Verification and safeguards

**121/121 regression tests pass** across V18–V27, including **18 V27-specific tests**. V27 tests check read-back, original-component byte preservation, catalogue counts and sortedness, strict malformed-input rejection, duplicate ID rejection, authentic Wii hash, source data fingerprint protection, and conversion determinism.

The command-line writer only accepts the **exact verified source SHA-256** for the V26 prototype and the **exact verified original Carbon 29-object test chunk**. It will not edit an arbitrary game stream. Files generated here are detached experimental chunks and cannot be installed directly.

The resulting sample is at `samples/Carbon_PC_Lights_PLUS_UC_RedBuilding_V27_OFFLINE.chunk`, and diagnostics are in `V27_NATIVE_IDENTITY_APPEND_REPORT.json` and `V27_IDENTITY_AUDIT.json`.

## Reproduce safely

Run from this source folder with Python 3.10+ (no game installation required):

```bash
python -m unittest test_v18 test_v19 test_v20 test_v20_transplant test_v21 test_v22 test_v23 test_v24 test_v25 test_v25_groups test_v26 test_v27 -v
python carbon_pc_identity_v27.py \
  samples/lights_carbon_pc.chunk \
  samples/Undercover_RedBuilding_Native_PC_MaterialRebind_V26.chunk \
  samples/undercover_redbuilding_wii.chunk \
  --output samples/Carbon_PC_Lights_PLUS_UC_RedBuilding_V27_OFFLINE.chunk \
  --report V27_NATIVE_IDENTITY_APPEND_REPORT.json
python audit_identity_v27.py --samples samples --output V27_SAMPLE_IDENTITY_CHECK.json
```

A full-stream *read-only* ID census requires a **user-supplied extracted** Carbon PC `STREAML5RA.BUN`:

```bash
python audit_identity_v27.py --samples samples \
  --pc-stream 'path/to/STREAML5RA.BUN' --output V27_IDENTITY_AUDIT.json
```

## Remaining blockers, in order

1. **World sector/stream registration:** rebuild the engine's external sector and stream index/relocations. Currently only one independent `0x80134000` chunk is rebuilt, with no referencing world entry.
2. **Scenery material/shader correctness:** imported mesh still has donor shader flags and a donor dependency beyond the original Wii hash.
3. **LOD grouping and transform placement:** one 1B model is inserted; original 1C/1Z, instance records and visibility/LOD groups are not yet integrated.
4. **Collision and road navigation:** not migrated.
5. **Game-side smoke test:** only after strict validation in a backed-up Carbon PC test copy.

The user-provided five game builds are still the source of truth. The new native identity-writer approach has concrete file-format evidence but does **not** yet prove Carbon PC can render or drive through Tri-City Bay.
