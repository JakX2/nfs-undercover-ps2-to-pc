# Cross-game gameplay record identities and NrtP two-section tables

**Status:** offline, read-only evidence on the owner's supplied Carbon PC, Carbon PS2, and Undercover PS2 GLOBAL archives. **Not** a playable port, working race converter, or verified relocation ABI.

## Reproduce

From the repository root with Python 3.10+ and locally supplied archives:

```sh
python research/global_vpak/resource_identity.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python research/global_vpak/pointer_sections.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

Both tools are standard-library-only, reject malformed structures, do not modify sources, and report only aggregates and three shared cross-game resource names. They **do not export archives, binary data, or complete resource-name inventories**.

## 1. NpeD resource identity

Every `NpeD` block in the 767 GAMEPLAY records from four source variants passes all checked invariants:

- Starts with `NpeD`, followed by 16-byte-aligned declared total size.
- Word at +8 equals 2, +12 and +16 are stable 32-bit identifiers, +20 is zero.
- Word at +24 is the byte length of the first zero-terminated filename; two equal-length ASCII filenames start at +28.
- Both filenames have the same basename, one `.vlt` and the other `.bin`; remaining bytes are zero padding.

The pair of 32-bit identifiers is **not** yet independently proven to be any particular hash algorithm. Its exact values match for each shared resource across platforms.

**Carbon PC backup and Carbon PS2:** all 190 resource-name pairs match at the same zero-based index, and all 190 have identical identifier pairs.

**Carbon vs Undercover:** exactly three name pairs are shared in the inspected GAMEPLAY inventories:

| Resource basename | Carbon PC / PS2 index | Undercover PS2 index | Carbon NpxE entries | Undercover NpxE entries |
| --- | ---: | ---: | ---: | ---: |
| `gpcore` | 169 | 166 | 2,105 | 2,171 |
| `race_bin_challenge` | 174 | 183 | 105 | 100 |
| `race_bin_quickrace` | 180 | 186 | 34 | 20 |

All three share both identifier words across platforms. The **different NpxE entry counts** show that even the named counterparts are not trivially interchangeable.

No Undercover resource pair occupies the same zero-based position as its Carbon counterpart.

## 2. NrtP section-table grammar

Every one of the 767 checked `NrtP` blocks can be read as a header, 12-byte triples, a zero triple sentinel and zero padding to a 16-byte boundary.

Each block contains exactly two ordered marker rows:

```text
(0, 0x00010002, 0)             # first group
(source_u32, 0x00010003, value_u32) ... 
(0, 0x00000002, 0)             # second group
(source_u32, 0x00010003, value_u32) ...
(0, 0, 0)                       # terminator; zero padding follows
```

The middle word of every non-marker row is `0x00010003` and the first word is 4-byte aligned. The first group values all fall within the record's pre-auxiliary text-region length; they include named strings **and** additional non-string data.

**Correction from the subsequent object-span audit (2026-11-03):** The following `NtaD`-length comparison columns are **historical diagnostics using the wrong offset base**, not actual out-of-bounds references. Group A source offsets are relative to the text-region start, while group B source offsets are relative to the start of `sreV`. Both groups target the text region. With the corrected bases, all 97,064 source slots and targets are in bounds and the source words are zero. See [OBJECT_REFERENCE_MAP.md](OBJECT_REFERENCE_MAP.md).

| Source | Records | First-group rows | Second-group rows | First-group targets beyond initial ErtS | Second-group target values beyond NtaD length |
| --- | ---: | ---: | ---: | ---: | ---: |
| Carbon PC active | 190 | 6,171 | 19,946 | 312 | 57 |
| Carbon PC backup | 190 | 6,171 | 19,946 | 312 | 50 |
| Carbon PS2 | 190 | 6,169 | 19,940 | 312 | 50 |
| Undercover PS2 | 197 | 4,557 | 14,164 | 455 | 2,168 |
| **Total** | **767** | **23,068** | **73,996** | **1,391** | **2,325** |

Other observed exceptions: **1,720** first-group source offsets and **2,359** second-group source offsets exceed the raw `NtaD` chunk length (counting a four-byte value). These are **not** automatically malformed records. They are evidence that a naïve, uniform `NtaD`-relative interpretation is unsafe.

**Updated interpretation:** These tables strongly resemble two relocation-source domains with a common text-region target base. The source offset bases and NpxE object containment are now structurally validated (see `OBJECT_REFERENCE_MAP.md`). Whether Carbon's loader applies these entries as pointer fixups, and the precise semantics of targets, remain unverified.

## Next milestone

Use the exact three shared NpeD identities as a controlled comparison set. Independently determine where each NrtP source offset and target is measured from, using the `gpcore` / challenge / quickrace pairs, then validate against Carbon PC backup and PS2 before attempting any reversible writer or runtime experiment.

**Testing:** eight new NpeD and fourteen new NrtP synthetic tests passed locally; in the local research worktree all 40 relevant synthetic tests passed. The proprietary archive checks passed for all four source variants. No game data, audio, graphics, executable patches, or extracted binary chunks are included.
