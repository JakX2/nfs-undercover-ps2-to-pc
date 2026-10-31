# V34: Experimental native Black Box IDX offset-table auditor

**Status (31 October 2026): 232/232 synthetic Python regression tests passed, plus the separate official vgmstream real decoder CI job. The original Undercover PS2 native IDX has NOT been tested.**

## Actual external format evidence

A [2023 ResHax original Xbox Carbon extraction discussion](https://reshax.com/topic/160-help-extract-big-file-nfs-carbon-xbox-version/) provides a working QuickBMS script by BloodRaynare for a Black Box IDX/BIG speech-bank pair. It reads:

- A 32-bit count at **IDX byte offset 0x54**.
- **16 bytes per record**, consisting of four 32-bit values: `ID`, `UNK`, `UNK2`, and `OFFSET`.
- `OFFSET` as the start of a source in the paired BIG.
- The next record's offset as the end boundary, and the BIG file length as the final boundary.
- Byte order guessed from the first 32-bit value, rather than hardcoded.

The author tested this recipe for **NFS Carbon on the original Xbox**, not Undercover PS2. Consequently, V34 treats it as a **hypothesis to validate against private Undercover source files**, not a known native Undercover PS2 format.

Do not assume `ID` means group ID, event ID, substream, CSI ID or anything else. V34 preserves the three undocumented words as `raw_id`, `unknown_1`, `unknown_2` and never sends them to V33 as invented group mappings.

## New V34 experimental tool

[experimental_native_idx_audit_v34.py](../tools/experimental_native_idx_audit_v34.py)

The tool reads both IDX and BIG **without modifying either**. In `--endian auto` mode it attempts both little- and big-endian interpretations and accepts only a **unique plausible** table that has a bounded count and strictly increasing, in-bounds source offsets. If no unique interpretation exists, it fails instead of guessing.

Each IDX record gets a span from its offset to the next indexed offset. V34 probes the first chunk at exactly that offset with the V31 `SCHl` parser, which only accepts the tested **PS2 platform 5, header version 3, mono EA-MT10 codec2=4** profile. The report distinguishes:

- `exact_schl_span`: Indexed span equals the original parsed SCHl length.
- `schl_within_padded_idx_span`: SCHl terminates before the next indexed offset; padding or another unexplained region exists.
- `schl_extends_beyond_index_span`: SCHl extends past the indexed boundary, so the table and stream layout conflict.
- `not_supported_mono_ps2_v3_mt10_schl`: No compatible source starts exactly at the indexed offset. This does not prove the IDX is wrong; it might reference stereo, other codecs or a different container arrangement.
- `not_probed`: Explicit probe limit excluded the row.

Because the IDX structure is **not yet validated for Undercover PS2**, even a matching native file would support only the index offset/spanning hypothesis. It would not establish event identity. A native V34 record must NOT be supplied as V33 group/substream data without an independently supported mapping.

## Run on a privately extracted original IDX/BIG pair

From the repository root on Windows PowerShell, adjust both file paths to the actual extracted file names:

    python audio/tools/experimental_native_idx_audit_v34.py audit --idx "D:\NFS_UC_PS2\SOUND\SPEECH\YOUR_FILE.IDX" --big "D:\NFS_UC_PS2\SOUND\SPEECH\YOUR_FILE.BIG" --endian auto --report "D:\NFS_AUDIO_LAB\v34_idx_audit.json"

Undercover's exact path and basename above are **not confirmed**, and should not be inferred from this example. Unpack the original split ZIP privately first.

The report contains numeric index fields, source size, source IDX SHA-256, original BIG offsets and counts, SCHl match statuses and sample counts. It **does not export raw audio, WAV or ASF**, and refuses to overwrite an existing report. The IDX source is not modified.

For a large index, add `--probe-limit 500` to inspect the first 500 indexed streams; untested rows remain explicitly marked `not_probed`.

## Synthetic independent validation

To run the standalone test with an installed upstream decoder:

    python audio/tools/experimental_native_idx_audit_v34.py self-test --decoder /path/to/vgmstream-cli

It creates a purely original synthetic IDX containing two 16-byte index entries and a BIG containing two independent generated EA-MT10 SCHl recordings. The first indexed span has **19 bytes of zero padding** after the SCHl; the second ends exactly at the BIG boundary.

The V34 parser recognizes both offsets and classifies **one padded span and one exact span**. The V31/V28 pipeline then extracts and decodes the two generated source streams under both EA platform headers using the actual official vgmstream CLI, with exact PCM equivalence.

Observed synthetic decoder results:

- 2 IDX records.
- 1 exact SCHl index span.
- 1 padded SCHl index span.
- 2/2 synthetic PS2/experimental-PC PCM pairs matched.
- Decoded PCM SHA-256: `4881991e5814b8e901efa85c44d4ab0c6c7b610b5ea8413b90c7c972b9ade1d6`.
- No original game assets were used or exported.

CI verification: https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41216490127

Automated tests: **232/232** synthetic Python tests passed, including 23 new V34 test cases covering endian detection, duplicate offsets, truncated index data, padding, invalid SCHl data, opaque IDs, no-overwrite and no audio export.

## Important game-edition distinctions

The V34 format hypothesis comes from an **original-Xbox Carbon** example. Separately, community analysis of **Undercover next-generation police speech** describes HDR/STH/DAT with EA Layer 3 audio. Those reports do not establish the layout of the **Undercover PS2/Wii EA-MT10 banks** being researched in this port. See [HCS vgmstream discussion](https://hcs64.com/mboard/forum.php?showpage=187&showthread=8687).

## Unresolved, not claimed

- Actual Undercover PS2 IDX count offset and 16-byte record hypothesis.
- Whether `raw_id` maps to a source group, sound identity, category, or something else.
- Verified original IDX -> EVT -> CSI linkage for a named PS2 police event.
- Actual original Undercover police voice decoded and heard, V28 PC-style exact PCM comparison using its original stream.
- Carbon PC game runtime accepting 22,050 Hz MicroTalk, the intended bank structure and the police event mapping.

The Project's earlier V21 archive is registered, but this turn's local Python/container runtime still fails before its contents can be examined, so no claim of original-archive verification is made. The tool is designed to be applied privately when that execution path is available.

**Next engineering milestone:** test V34 against the original Undercover PS2 IDX/BIG. If the 0x54 profile is rejected, inspect the real IDX bytes using the earlier verified V1–V21 parser rather than weakening checks to force a match.