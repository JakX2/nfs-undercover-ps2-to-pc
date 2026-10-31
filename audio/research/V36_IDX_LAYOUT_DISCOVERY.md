# V36: Infer candidate native IDX layouts from verified EA SCHl offsets

**Status:** Tested with original copyright-free synthetic data and the actual V31 raw EA SCHl scanner. The original Undercover PS2 IDX format is **not yet established** and no genuine Undercover police recording has been decoded in this session.

## Why this is more useful than assuming the Xbox IDX layout

V34 implemented a public QuickBMS extraction recipe from [ResHax for Carbon on original Xbox](https://reshax.com/topic/160-help-extract-big-file-nfs-carbon-xbox-version/). It reads a count at IDX byte offset `0x54`, 16-byte records, and the BIG offset at the fourth 32-bit word in each record.

The public author explicitly demonstrated the recipe on the **Xbox version of Carbon**, not the PS2/Wii edition of Undercover. The 2018 discussion of Undercover HDR/STH/DAT police audio concerns **a different platform-specific format** and is not proof of PS2 IDX structure. See [HCS discussion](https://hcs64.com/mboard/forum.php?showpage=187&showthread=8687).

The Project's original V21 research ZIP is registered, but Python/container access to its bytes remains unavailable. Instead of pretending that V34's format is the PS2 answer, **V36 tests multiple plausible table shapes against independently scanned SCHl offsets**.

## New source

- [V36 discovery tool](../tools/native_idx_layout_discovery_v36.py)
- [V36 synthetic tests](../tests/test_native_idx_layout_discovery_v36.py)
- [V31 actual SCHl scanner](../tools/undercover_big_voice_scan_v31.py)

V36 consumes the user's privately extracted native `IDX` and a **V31 metadata-only scan JSON** produced from its corresponding `BIG`. It does not itself read or copy any original compressed audio or BIG bytes.

Within explicitly bounded combinations it tries:

| Tested parameter | V36 search space |
| --- | --- |
| Candidate count-field offset | Aligned bytes `0x00..0x80` |
| Gap from count offset to row table | 4, 8, 12, 16, 20, 24, 32, 48 or 64 bytes |
| Record stride | 8, 12, 16, 20, 24 or 32 bytes |
| Offset-column position | Every 32-bit aligned column within the record |
| Byte order | Little-endian or big-endian |
| Entry count | 3 through 100,000, bounded by remaining IDX length |
| Evidence threshold | At least three distinct validated SCHl offsets and 75% of sampled table rows |

For large indexes, V36 samples up to 96 rows spread across the candidate table, including early, middle and last entries. It compares the proposed numeric offsets to original SCHl starts validated by V31. Record-order monotonicity is reported, not assumed: an index may be sorted by opaque IDs rather than BIG offset. The output ranks candidates by sample coverage, distinct matched offsets, and unexplained trailing IDX bytes.

**A high score is a hypothesis for further inspection, not proof of a native EA schema.** The 75% criterion is a conservative diagnostic filter; it can miss a genuine layout when the scanned BIG contains other codecs, stereo, or audio structures that V31 does not support. A candidate can also be a false positive or an alias of another hypothesis.

V36 cannot determine the native meaning of group IDs, substreams or any opaque IDX fields, and **must not** export a purported V33 group/EVT/CSI mapping based on the guessed offset column.

## Run with the real files in your private workspace

First perform the V31 scan against a privately extracted original PS2 BIG:

    python audio/tools/undercover_big_voice_scan_v31.py scan --big "D:\NFS_UC_PS2\SOUND\YOUR_FILE.BIG" --max-results 20000 --report "D:\NFS_AUDIO_LAB\scan_v31.json"

Then run V36 against the matching local IDX:

    python audio/tools/native_idx_layout_discovery_v36.py discover --idx "D:\NFS_UC_PS2\SOUND\YOUR_FILE.IDX" --scan "D:\NFS_AUDIO_LAB\scan_v31.json" --top 10 --report "D:\NFS_AUDIO_LAB\idx_layout_v36.json"

The above filenames/locations are placeholders. No original archive filename or game-root location was confirmed here. Input IDX and scan JSON remain unchanged. The report path **must not exist**. The generated report includes only schema hypotheses, sample match metrics and input hashes.

If zero layouts qualify, the result is **no qualifying candidate in the searched combinations**, not evidence the IDX lacks SCHl references. In that case, inspect the actual V21 source parser, other index layouts or V31's mono-only scan coverage rather than weakening tests to manufacture a result.

## Verified original synthetic test

Run:

    python audio/tools/native_idx_layout_discovery_v36.py self-test

V36 generates two entirely artificial IDX tables:

- Xbox-like: little-endian count at `0x54`, 16-byte record stride, fourth word as BIG offset.
- Alternate: big-endian count at `0x10`, 12-byte record stride, second word as BIG offset.

It discovers both hypotheses with bounded candidate search. In a separate integrated fixture, it builds an original copyright-free mock BIG containing multiple genuine synthetic PS2-v3 MT10 SCHl streams. The **actual V31 parser** independently scans their real start offsets, and V36 discovers the matching artificial IDX layout from those offsets. No game assets, fake police dialogue or original extracted audio are published.

### Verified CI

The GitHub CI suite passes **291/291 Python synthetic tests**, plus the existing separate upstream vgmstream decoder integration and V36 self-test. All tests are source-only and game-free.

CI evidence: https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41220098460 (291/291 synthetic tests passing, with the official upstream decoder job passing separately).

## Still unverified

- The genuine Undercover PS2 native IDX count field, stride and offset-column position.
- Real IDX offsets joined to original PS2 mono EA-MT10 SCHl from the user-owned source bank.
- Correct mapping from native IDX group/substream to EVT/CSI police event.
- A genuinely extracted and heard Undercover dispatch voice, decoded before/after PC-style header conversion.
- Carbon PC sound bank loading and original police-radio runtime playback.

**Next gate:** Run V31 and V36 with real source IDX/BIG, compare any high-coverage candidate against the recovered authentic V21 parser, and inspect the resulting event relationships before any game installation is changed.