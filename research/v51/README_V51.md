# V51 | ROOT-relative 96-byte scenery-instance alignment (Wii fixture)

V51 fixes the **candidate 96-byte instance reader in V49**. Previously it assumed
that the 0x34103 child payload length was exactly divisible by 96 and that the
first instance started at offset zero within the payload. This incorrectly
rejected the authenticated 8,488-byte Undercover Wii RedBuilding scene.

## Verified original-source finding

- Source: Original UC Wii RedBuilding 0x80034100 scene ROOT.
- SHA-256: `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`.
- Child 0x34103 instance payload starts at **ROOT-relative byte 92**.
- The first **4 bytes are `11 11 11 11`**. Their function is *not* proven.
- The first instance begins at ROOT-relative byte **96**, aligned to 16.
- Child length **2,980 = 4 + 31 * 96** bytes. Thirty-one original instances follow the prefix.
- In the same source scene, instance slot 26 has scenery-info index 8 and preculler index 20.

These are observations about **one verified Wii serialization**. They do not establish the Carbon PC on-disk field layout, alignment rule, or runtime object allocation.

## Code change

`research/v49/v49_native_culling_gate.py` now computes its **candidate** 16-byte alignment padding from the original ROOT-relative 0x34103 payload start, not by demanding `% 96 == 0` on the entire child payload. Its candidates remain marked as speculative for Carbon PC.

Every original byte is kept in memory unchanged. The implementation is read-only. It cannot patch game files, and it never claims that an append with an unchanged tree is installable.

## Tests

`test_v51_alignment.py` contains 15 synthetic public tests covering all four 16-byte padding residues (0/4/8/12), big-endian framing, nonzero opaque padding, malformed instance lengths, one-instance append detection, unchanged-tree coverage rejection and no-install guarantees.

Four additional tests execute **only when** `NFS_UC_WII_SCENE` points to the exact original Wii 8,488-byte scene with the pinned SHA-256. This file must stay local. The GitHub Actions workflow intentionally runs synthetic tests and skips proprietary fixture tests.

```sh
cd research/v51
python -m unittest test_v51_alignment -v
NFS_UC_WII_SCENE=/path/to/UC_Wii_RedBuilding_Original_Scene.chunk python -m unittest test_v51_alignment -v
```

## Next map/world conversion gates

1. Obtain and fingerprint original Carbon PC world scene roots and authentic V42 donor/candidate data.
2. Determine actual Carbon PC instance alignment and 0x34105/0x34107 serialized schemas from multiple roots and code, rather than carrying Wii-specific rules into a writer.
3. Update spatial membership and preculler visibility records only after their format, loader behavior, section ownership, relocation and material references are verified.
4. No live installation until validation of textures, collision, navigation, streaming and in-game rendering.