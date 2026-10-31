# V55: source-gated cross-root scenery layout discriminator

**Scope:** NFS Undercover PS2/Wii → Carbon PC, **Map & World Conversion / Geometry**, offline and **read-only**. The new tool enables side-by-side investigation of *independently supplied* scenery ROOTs without distributing original game bytes. It does not decode `0x34107`, prove the Carbon PC disk ABI or create an installable mod.

## Why this milestone matters

The single exact original Wii RedBuilding scenery ROOT has SHA-256:

`cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`

Its candidate layout is:

| Field/chunk | Authenticated original Wii scene observation |
|---|---:|
| ROOT byte length | 8,488 |
| Candidate `0x34103` 96-byte instance records | 31, after 4-byte root-relative alignment prefix |
| Candidate `0x34105` 48-byte hierarchy nodes | 8 |
| Candidate `0x34107` 128-byte blocks | 24 |
| Candidate `0x3410D` 32-byte auxiliary records | 31 |
| `0x34107` byte length | 3,072 |

This source supports *both* simple arithmetic hypotheses for the **same** `0x34107` payload length:

- `(31 candidate instances + 1) × 96 = 3,072` bytes;
- `8 candidate tree nodes × 384 = 3,072` bytes.

Neither arithmetic match identifies semantics. The `24 × 128` segmentation is also a **candidate**. The child `0x34101` first `u32` happens to be `0x00000000` in this fixture; it is **not** proven to be a geographic section identifier and must not be equated with a separate Carbon master-stream section ID.

## What's new in V55

`v55_cross_scene_hypothesis_gate.py` reads a **local JSON manifest** of ROOTs or ROOT offsets in larger streams. For each entry it requires both an exact **whole-file SHA-256** and an exact **extracted-root SHA-256**, plus explicit byte order. It strictly parses bounded direct child chunks, reports candidate instance/node/aux/preculler counts, and tests competing length equations **independently**.

The cross-root report:

- Deduplicates byte-identical ROOT hashes, so copies of one scene never increase the evidence count.
- Flags groups with an identical `0x34101` first word **and** identical `0x34103` instance payload even when other bytes have changed, which is a red flag for edited/near-duplicate inputs.
- Reports structural candidates for unknown files and user-labeled Carbon PC files, but **never accepts a user platform hint or a distinct hash as independent original-game provenance**.
- Refuses a report path that would overwrite inputs, the manifest or an existing report. It writes only JSON counts, candidate arithmetic results and hashes, not private paths or game bytes.

The asset-free test suite uses **synthetic** roots with size relationships arranged so the `instance+1` hypothesis alone fits, the `nodes×384` hypothesis alone fits, both fit, or neither fits. Those cases **prove the gate discriminates formulas**, not that any original game uses the synthetic layouts.

## Local input format

Example private `manifest.json` using a standalone ROOT that you already fingerprinted:

```json
{
  "roots": [
    {
      "label": "wii_sector_original",
      "path": "/your/local/scenes/original_wii_scene.chunk",
      "endian": "little",
      "platform_hint": "wii",
      "expected_file_sha256": "cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f",
      "expected_root_sha256": "cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f"
    }
  ]
}
```

For a source ROOT embedded in a larger original `.BUN`, set `offset` to a known integer byte offset (JSON number); the whole-file and ROOT digests will **differ**. Do not guess the ROOT digest or reuse a standalone digest for an unrelated donor. `platform_hint` means exactly *user-provided hint*, not verified authenticity. Use a new report filename each run:

```bash
python research/v55/v55_cross_scene_hypothesis_gate.py \
  --manifest /private/manifest.json \
  --report /private/v55_report_new.json
```

To run public synthetic tests, no original files are required:

```bash
python -m unittest discover -s research/v55 -p 'test_v55.py' -v
```

To run pinned original-Wii tests using your own local fixture:

```bash
NFS_UC_WII_SCENE=/private/UC_Wii_RedBuilding_Original_Scene.chunk \
  python -m unittest discover -s research/v55 -p 'test_v55.py' -v
```

## Evidence and limitations

- **34** asset-free synthetic tests and **7** pinned original-Wii fixture tests passed locally: **41/41** V55.
- Previously selected offline V41, V43–V46, V50, V52–V54: **284/284** independently rerun, combined **325/325** selected tests. **V51 fixture-level direct V49 reader test remains a separately tracked gap**; do not fold it into these counts.
- Only **one** independently authenticated original Wii scenery root is available here. Other copies have identical SHA and are not independent sectors.
- No original Carbon PC world stream, source-authenticated V42 donor/modified ROOT pair, or verified PC loader callback was provided. Therefore **cross-scene replication and any Carbon PC disk-layout decision remain blocked**.
- No gameplay test, world insertion, spatial/preculler writer, shader/texture resolution, collision or navigation is included. **Not safe to install.**

**Next:** supply a second independently authenticated original Wii scenery sector whose instance and hierarchy counts differ, then test these equations on both originals; independently validate real Carbon PC root layouts before building native spatial records.