# NpxE object spans and NrtP pointer-source domains

**Status: offline, read-only structural validation.** No native PC game loader, field semantics, memory relocation behavior, race logic or playable port has been verified.

This research builds on the earlier six-chunk GAMEPLAY VPAK audit. All data came from the owner's local game archives; **no original game bytes, names beyond the three already documented shared resource keys, executable patches or derived asset files are committed**.

## Run

Python 3.10+ from repository root with your own local archive copies:

```sh
python research/global_vpak/object_reference_map.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

The program prints aggregate statistics only. It rejects invalid chunk ranges, record-pointer source slots that are not zero, duplicate source slots, out-of-bounds targets, nonzero object padding and references that do not belong to a delimited object. The new suite contains **16 synthetic-only regression tests, all passing locally**. The full four-variant audit also passed in the local workspace.

## Precise base of NpxE object ranges

Let `aux = sreV || NpeD || NrtS || NtaD` (the four complete chunks, including their headers) and let `prefix = len(sreV) + len(NpeD) + len(NrtS)`.

In every GAMEPLAY record checked:
1. The first `NpxE` entry's word2 equals `prefix + 8`, exactly after the `NtaD` eight-byte header.
2. Each of the **21,224** entries has word0 = `0x8E112EB7`, a **strictly positive** four-byte-multiple length in word1, an eight-byte-aligned auxiliary-relative offset in word2, and a range entirely contained inside `NtaD`.
3. For each consecutive pair, `next.word2 = align8(current.word2 + current.word1)`, with only zero padding between ranges.
4. Bytes after the final entry's range to the end of `NtaD` are also zero padding.
5. The last entry has word3 = 0, all others have nonzero word3. **This is not an empty sentinel**: every last-marked entry itself has a positive length and valid object byte range.

The five earlier offset/length "beyond NtaD" anomalies at Carbon PC active indices 87/88 and Undercover indices 166/192/196 arose because we previously compared **auxiliary-relative offsets** directly against the length of `NtaD`. Correcting the base resolves all five. This changes the earlier interpretation and is recorded explicitly rather than hidden.

## NrtP has two source-address domains

Each record contains two ordered marker groups in `NrtP`. The triples remain structurally described as `(source_offset, 0x00010003, target_offset)`; calling them relocation references is a **well-supported hypothesis**, not yet a verified Carbon loader procedure.

**Group A:** source offsets are relative to the start of the pre-auxiliary text region and fall *after* the initial `ErtS` string pool. Every source points to a zero 32-bit word. Every target points inside the same text region. Exactly 21,677 targets fall at NUL-delimited string starts within `ErtS`. The remaining 1,391 targets lie after the initial string pool and satisfy `target = source + 4`.

**Group B:** source offsets are relative to the start of `sreV` (the start of `aux`). Every source lies inside exactly **one** `NpxE`-delimited range within `NtaD`, points at a zero 32-bit word, and has its target within the record's pre-auxiliary text region. Every delimited object has at least one such group B source. Of the 73,996 targets, 28,785 land at NUL-delimited initial string-pool offsets and 45,211 point to the later text region.

**Important:** The numeric values in the two groups share the *target* region, but **not** the same *source* offset base. Reading all source offsets relative to `NtaD` produced false out-of-bounds warnings in the previous research stage.

## Four-source validation

| Source | Records | Delimited NpxE ranges | Group A slots | Group B slots | Group B slots assigned to NpxE ranges |
| --- | ---: | ---: | ---: | ---: | ---: |
| Carbon PC active GAMEPLAY.BIN | 190 | 5,726 | 6,171 | 19,946 | 19,946 |
| Carbon PC backup GAMEPLAY.BAK | 190 | 5,726 | 6,171 | 19,946 | 19,946 |
| Carbon PS2 GAMEPLAY.BIN | 190 | 5,724 | 6,169 | 19,940 | 19,940 |
| Undercover PS2 GAMEPLAY.BIN | 197 | 4,048 | 4,557 | 14,164 | 14,164 |
| **Total** | **767** | **21,224** | **23,068** | **73,996** | **73,996** |

**All 97,064 inspected source slots contain zero-filled 32-bit words, with zero violations.** Every source is within its observed address domain; every target lies within the text region. The records also have 767 nonempty zero-marked terminal entry ranges. Exactly 21,224/21,224 objects have at least one group B source slot.

## Engineering next steps

- Use the verified span + reference association as a *read-only*, per-object graph for the three known cross-game resources (`gpcore`, `race_bin_challenge`, `race_bin_quickrace`).
- Distinguish references to NUL-delimited names from references to post-string structured text data; verify identifiers and field types against independent engine evidence.
- Validate platform version differences and object serialization before trying a **reversible in-memory synthetic fixture**. Never assume the presence of a bounded object span implies that its payload can be copied into Carbon PC.
- Preserve all original files and avoid writing executable/game archive patches until a reversible loader-compatible format is independently established.

**Note on earlier reports:** `EXPORT_TABLE.md` and `RESOURCE_AND_POINTERS.md` originally reported out-of-range offsets when tested against the wrong base. That interpretation is superseded by this audit; the prior data and historical notes remain for reproducibility.
