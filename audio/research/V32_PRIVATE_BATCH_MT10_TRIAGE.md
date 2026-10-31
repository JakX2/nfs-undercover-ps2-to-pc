# V32: Batch real-decoder triage for private PS2 MicroTalk recordings

**Status: source code and CI tested. The original game audio has not been decoded in this environment.** V32 is built to make that first private experiment much less manual.

## What it does

V31 discovered contiguous little-endian mono PS2-v3 EA-MT10 (codec2=4) SCHl streams inside a locally extracted BIG. V32 uses that V31 scanner to choose a *small batch* of candidates and runs an **independent vgmstream-cli decoded-PCM comparison for each one** against its V28 experimental PC-v2 header version.

V32 checks which candidates decode correctly and separately records failures. Unlike a structural-only scan, it **requires the real external decoder**. It never labels a recording as police dialogue: group/IDX/CSI/EVT attribution still needs actual source index/event evidence. Longer recordings are tried first by default, but duration is not evidence of voice content or event identity.

Behavior:
- The original .BIG is read-only and stays on the user's machine.
- Candidates are ordered by descending decoded sample count, then ascending BIG offset. Use --start for pagination.
- Default scan considers up to 1,000 compatible streams; default batch tests 8 of them; maximum decoded batch is 32 per run.
- A minimum sample threshold lets users skip extremely short clips.
- V31 privately extracts only one candidate at a time, V28 builds the experimental PC-style EA header without altering compressed data, and upstream vgmstream decodes both in a temporary folder.
- Temporary original clips, PC-shaped streams, and WAVs are deleted after each comparison.
- A NEW output folder contains **report.json only**, with source offsets, sizes, sample counts, block counts, decoded PCM hashes, and separate success/failure statuses. Errors omit private path strings.
- All results explicitly state that police event identity and Carbon PC runtime playback are **unverified**.
- A scan hitting its maximum reports scan_may_be_truncated=true, rather than claiming complete coverage.

## Run privately on an extracted Undercover BIG

First unpack the uploaded split archive privately using an archive manager supporting .z01/.z02/.zip. Locate an actual extracted BIG file. The filename below is a placeholder, not a filename confirmed from the archive.

From the repo root, on Windows PowerShell:

    python audio/tools/big_mt10_batch_triage_v32.py triage --big "D:\NFS_UC_PS2\SOUND\YOUR_FILE.BIG" --decoder "D:\Tools\vgmstream\vgmstream-cli.exe" --out-dir "D:\NFS_AUDIO_LAB\v32_private_triage" --max-results 1000 --limit 8 --minimum-samples 432

The new directory must not exist. Default no audio is retained. The report lists candidate streams as **unidentified MicroTalk candidates**, not proven police voices.

If needed, adjust --start 8 and use a different new --out-dir to test the next eight candidates.

Exit statuses: 0 when all selected candidates passed decoded-PCM checks; 1 when one or more selected candidates fail; 2 on an invalid source/decoder/output setting; 3 when no eligible candidates were selected. A successful result does NOT imply in-game Carbon PC compatibility.

## Reproduce V32's CI experiment with no game files

    python audio/tools/big_mt10_batch_triage_v32.py self-test --decoder /path/to/vgmstream-cli

The tool creates an original copyright-free synthetic BIG with an invalid decoy and two valid multi-frame EA-MT10 SCHl streams. Both contain the same generated audio packaged in one or three SCDl blocks. It then scans, selects, privately extracts, rewraps and **actually decodes** both using the independently installed upstream vgmstream CLI.

**Observed real decoder test:** 2 selected, 2 exact PCM matches. Original decoded PCM SHA-256: `4881991e5814b8e901efa85c44d4ab0c6c7c972b9ade1d6`.

**Observed regression tests:** 182/182 synthetic tests passed, including the new batch-selection, decoding-failure and no-overwrite coverage. Both CI jobs passed.

GitHub Actions evidence: https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41213209246

Source and tests:
- [V32 batch real-decoder triage](../tools/big_mt10_batch_triage_v32.py)
- [V32 regression tests](../tests/test_big_mt10_batch_triage_v32.py)
- [V31 single-stream BIG scanner](../tools/undercover_big_voice_scan_v31.py)

## What remains unresolved

**No original Undercover audio was tested in this CI run.** The user's split PS2 archive attachments are registered in the project, but the execution environment used to read the archive bytes still fails. V32 cannot prove police voice identification just from an SCHl offset or file length. That needs real original IDX/CSI/EVT event association, using the earlier V1–V21 research and real game files. Original Undercover group rebasing and an engine-accepted Carbon PC voice bank also remain unverified.

Please keep original, rewrapped and decoded game audio off public GitHub. Only code, synthetic fixtures and non-sensitive metadata belong in this branch. No game installation has been modified.