# Reversible private Carbon PC DXT1 stream-copy gate

**2026-11-04. Source-free implementation plus privately verified original-file copy controls. No in-game execution, installation, binary patch, archive repack, or runtime-acceptance claim.**

## The evidence boundary

The previous `pc_texture_header_overlay_gate.py` can alter one existing opaque DXT1 texture **inside an in-memory `0xB3300000` section**, preserving original descriptor/index/mipmap metadata and every other section byte. Carbon PC does not necessarily read standalone sections, however. To test that isolation at the surrounding stream-file level, `private_carbon_dxt1_stream_stage.py` reads the existing uncompressed `TRACKS/L5RB.BUN` section table (`0x34110`, 92-byte rows) and a matching `TRACKS/STREAML5RB.BUN` input, then constructs a private **same-length stream copy**. The original source files are never opened for writing.

This tool deliberately does **not** modify ZIP members. The owner's original Carbon PC `TRACKS.z01`/`.z02`/`.z03`/`.zip` set is a multi-volume archive with compressed members and CRC bookkeeping; an uncompressed stream copy is not a replacement ZIP volume. Nor is it proof that Carbon PC will load a loose test stream or that an altered DXT1 entry becomes visible during gameplay.

## New implementation

`private_carbon_dxt1_stream_stage.py`:

- Validates the bounded small bundle and stream files, requires exactly one `0x34110` table, forbids duplicate section IDs and overlapping target ranges, and limits target sections to known Carbon PC section IDs **141 or 142**. It extracts only the requested, table-bounded section from the uncompressed stream and checks the full PC texture metadata, 128-byte pixel alignment and filler.
- Chooses a **pre-existing DXT1** texture by zero-based *ordinal* among the section's sorted DXT1 entries. **Original texture hashes and names are neither displayed nor saved.** Constructs an opaque, synthetic solid RGB input, encodes the original mip count, and changes only that slot's existing image byte span. The source texture's original image byte count, dimensions and metadata are retained; a new identity is never inserted.
- Performs an in-memory reversal and requires byte-for-byte equivalence with the source section. Dry-run is the default, and creates **no file**.
- With explicit `--write-private-copy --private-output ...`, writes to a new temporary file in the output directory, verifies the **entire** staged stream byte for byte outside the selected image span, rechecks the original stream digest and size/mtime, then uses no-overwrite hard-link promotion. The output path must not already exist. Temporary files are removed after success or failure. This requires a filesystem supporting same-directory hard links, such as NTFS or ext4.
- Returns **aggregate-only JSON**, including selected section ID, original DXT1 slot count, changed image-byte count, original image span size, mip levels, and confirmation that the input is left untouched. Nothing prints the private texture identity, original bytes, image pixels or stream offsets.

### Source-free reproduction

From the repository root:

```sh
python -m unittest discover -s research/world_bridge \
  -p 'test_private_carbon_dxt1_stream_stage.py' -v
```

For *private owner files extracted from an original Carbon PC installation/archive*, first dry-run:

```sh
python research/world_bridge/private_carbon_dxt1_stream_stage.py \
  --bundle /private/carbon_pc/TRACKS/L5RB.BUN \
  --stream /private/carbon_pc/TRACKS/STREAML5RB.BUN \
  --section-id 141 --dxt1-slot 0 --solid-rgb FF00FF
```

Then, only when explicitly choosing to create a *new* private copy:

```sh
python research/world_bridge/private_carbon_dxt1_stream_stage.py \
  --bundle /private/carbon_pc/TRACKS/L5RB.BUN \
  --stream /private/carbon_pc/TRACKS/STREAML5RB.BUN \
  --section-id 141 --dxt1-slot 0 --solid-rgb FF00FF \
  --write-private-copy \
  --private-output /private/sandbox/STREAML5RB_PRIVATE_TEST.BUN
```

**Do not publish the output.** It is almost entirely the owner's original game stream. The original stream is already a pristine rollback source; deleting the staged private test copy reverses this offline experiment without touching the installation. Any future actual game installation experiment needs separate, verified loading instructions and a backup; this stage does not attempt to move/overwrite an installation file.

## Synthetic tests

`test_private_carbon_dxt1_stream_stage.py` has **31/31** passing synthetic-only tests, exercising source-free section tables and texture-pack fixtures, two stream sections, multiple mip levels, exact pixel-span isolation, full-file copy verification, byte-perfect in-memory reversal, default dry-run, explicit-write protection, existing output refusal, symlink refusal, missing output directory, malformed section rows, out-of-range offsets, duplicate/ambiguous table data, corrupted alignment, corrupt staged output and temporary-file cleanup.

The focused combination of this module, `test_pc_texture_header_overlay_gate.py`, `test_synthetic_dxt1_texture_writer.py`, `test_synthetic_pc_dxt1_pack_envelope.py`, and `test_pc_dxt_reference_decode.py` passes **102/102 tests locally**. GitHub CI is not claimed.

## Original Carbon PC archive controls

In a private working directory, the owner's Carbon PC split `TRACKS` archive was decompressed with independently checked uncompressed sizes **and ZIP CRCs**, for `L5RB.BUN` and `STREAML5RB.BUN`. The extracted stream is **82,837,504 bytes**. The new source-only tool then ran both dry-run and *private* full-file copy checks against two existing DXT1 texture slots:

| Original section | Existing DXT1 slots | Test image span bytes | Mip levels | Changed bytes inside span | Full private stream copy |
|---|---:|---:|---:|---:|---|
| 141 | 30 | 43,680 | 6 | 41,893 | Passed |
| 142 | 40 | 21,824 | 5 | 21,372 | Passed |

For **both** separate copies: exact original stream size preserved; all bytes outside the selected image span unchanged; the existing texture metadata and section-table bytes preserved; the original extracted stream remained untouched. Original archive data, image bytes, texture hashes and produced private stream copies are **not** committed, attached or uploaded. This is **not a successful in-game texture replacement**.

## Next runtime gate

A genuine game-side test would require establishing how Carbon PC selects the uncompressed `STREAML5RB.BUN` from its installed data and whether it accepts a modified image span from the corresponding `L5RB.BUN` table. Only after a reversible private installation test and visual confirmation can we claim a visible texture replacement. New Undercover identities, alpha-sensitive materials, new resource registration, collision and world integration remain separate unfinished work.
