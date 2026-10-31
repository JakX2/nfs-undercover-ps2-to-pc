# V33: Evidence-based IDX / EVT / CSI attribution for scanned audio

**Status (2026-10-31): 209/209 synthetic regression tests passed in GitHub Actions, and the official vgmstream codec integration job passed.** This is a **metadata join**, not the long-awaited genuine Undercover voice decode.

## Problem solved

V31 finds compatible PS2 mono EA-MT10 SCHl streams inside a local extracted BIG and V32 can privately decode and compare a batch of them after experimental PC-header conversion. But an SCHl offset alone **cannot tell us which police dispatch event, if any, owns that stream**.

V33 adds an **explicit evidence chain** between five independent kinds of information:

1. **V31 scanner JSON:** A validated original BIG offset, SCHl stream length, sample count, and SCDl block count.
2. **IDX export CSV:** Which original source group and substream references that BIG offset, and its recorded length when available.
3. **EVT export CSV:** Which source event IDs link to which group IDs.
4. **CSI export CSV:** Event ID, event name, and an operator-supplied classification (`police`, `other`, or `unknown`).
5. **Optional V32 triage JSON:** Which matching offset/length pairs passed a real independent original-versus-PC-shaped decoded PCM comparison.

**Critical:** This tool does *not* reverse engineer the IDX, EVT or CSI binary layout. The CSV must come from separately verified local original-file exports, using the earlier V1–V21 research. No original IDX/CSI/EVT bytes were available for testing this turn. Do not substitute made-up event names, offsets, or group IDs for actual exports.

## Required CSV schemas

The CSV schemas are **V33 intermediate exchange formats**, not claims about the actual on-disk EA structures.

IDX export (`idx.csv`):

    group_id,substream,big_offset,stream_length
    42,0,101,110

EVT export (`evt.csv`):

    event_id,group_id
    EXAMPLE_EVT_A,42

CSI export (`csi.csv`):

    event_id,event_name,classification
    EXAMPLE_EVT_A,Synthetic example only,police

The values above are **invented training/test examples**, not actual Undercover event IDs. The CSV classification comes from the person preparing the source export; `police` does **not** mean audio was heard, game routing confirmed or an event independently identified.

IDs and BIG offsets can be decimal or `0x` hexadecimal. If the IDX exporter provides an offset but not a trustworthy stream length, leave `stream_length` blank. Such a join is flagged **`offset_only`**, never an exact byte-range match. Never infer the IDX length from the scan merely to force an exact match.

## Private local workflow

Run V31 against a privately extracted original source BIG and save the scan metadata:

    python audio/tools/undercover_big_voice_scan_v31.py scan --big "D:\NFS_UC_PS2\SOUND\YOUR_FILE.BIG" --report "D:\NFS_AUDIO_LAB\v31_scan.json"

Optionally use V32 with the official decoder to test the actual PCM privately:

    python audio/tools/big_mt10_batch_triage_v32.py triage --big "D:\NFS_UC_PS2\SOUND\YOUR_FILE.BIG" --decoder "D:\Tools\vgmstream\vgmstream-cli.exe" --limit 8 --out-dir "D:\NFS_AUDIO_LAB\v32_batch"

Use source IDX/EVT/CSI extraction research to create the three CSVs. Then join all metadata:

    python audio/tools/idx_evt_csi_evidence_join_v33.py join --scan "D:\NFS_AUDIO_LAB\v31_scan.json" --triage "D:\NFS_AUDIO_LAB\v32_batch\report.json" --idx "D:\NFS_AUDIO_LAB\idx.csv" --evt "D:\NFS_AUDIO_LAB\evt.csv" --csi "D:\NFS_AUDIO_LAB\csi.csv" --report "D:\NFS_AUDIO_LAB\v33_attribution.json"

V32's `--triage` argument is optional. Without it, `decoder_pcm_status` is explicitly `not_decoder_tested`. The new V33 output path must not exist and is never overwritten. All input tables remain read-only and are SHA-256 fingerprinted in the result for reproducibility. V33 does not read or write any game audio.

## What counts as a meaningful link

- `offset_and_length`: IDX points to the same offset **and** the same recorded stream length as V31's scan; strongest **structural** evidence.
- `offset_only`: IDX points to the same offset but has no independent length; insufficient for a strong byte-range claim.
- `offset_but_length_mismatch`: IDX has a different declared length; events are deliberately **not** attached to that entry until the mismatch is explained.
- `event_links`: EVT associates an indexed group with one or more events; CSI supplies names only when corresponding event IDs are present.
- `classification_supplied=police`: The **export preparer's label**. Even when exact IDX/EVT/CSI joins and V32 PCM hashes match, the result is still *a police-labeled candidate*, not a confirmed dispatch voice.

**Many-to-many associations are preserved.** A sound group can have multiple substreams and several events. Multiple IDX entries may alias the same offset; these are reported, not arbitrarily deduplicated. Duplicate group+substream records, duplicate CSI event IDs, duplicate EVT edges, duplicate V31 offsets, and contradictory V32 PCM hashes are rejected.

V32 results are cross-checked against the exact V31 offset and stream length. A scan is not proof that it came from a particular game: even all joins passing leaves `original_game_provenance_independently_verified=false`, `actual_police_voice_heard_or_confirmed=false`, and `carbon_pc_runtime_verified=false`.

## Verified synthetic CI

V33's 27 new tests use invented IDX/EVT/CSI records alongside generated V31/V32-style metadata. They cover event-chain mapping, one-to-many associations, offset-only links, bad lengths, missing CSI names, contradictory PCM results, conflicting IDs, safe outputs, and no false police-voice certification.

**Observed:** 209/209 synthetic Python tests passing, plus upstream real-vgmstream decoder integration passing in the separate CI job. V33 itself is a metadata graph tool and does not need the decoder to run.

Verification: https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41215619199

Source: [V33 joiner](../tools/idx_evt_csi_evidence_join_v33.py) and [V33 regression tests](../tests/test_idx_evt_csi_evidence_join_v33.py).

## What's still blocking real police speech

1. **Original IDX/EVT/CSI exports:** The V1–V21 research ZIP is still present in this project, but this session's local Python/container runtime failed to read it; V33 therefore relies on manually supplied trusted CSV exports instead of pretending those binary layouts are decoded here.
2. **Real original voice:** No genuine Undercover police recording has been independently decoded and heard in this turn, despite successful synthetic MT10 decoding in V27–V32.
3. **Actual PC engine:** No proven Carbon PC native MT10 voice bank, police event routing, or audible in-game dispatch.

Next: recover the original research parsers, create authentic original-file CSV exports, and run V31–V33 on one private source bank. Once a named police-labeled candidate and real decoded PCM are found, the user can listen to the local WAV and confirm the recording's true content before a controlled Carbon PC runtime test.

**Never upload original game audio, decoded voice WAVs, private bank files or fake event assignments to public GitHub.**