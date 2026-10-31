# V35: Safe recovery of the original V1–V21 audio-research source archive

**Status (2026-10-31): source-recovery tool is committed, 263/263 synthetic unit tests passed, and the independent official vgmstream integration job passed. The actual user-owned V21 research ZIP was not inspected by the GitHub runner or this local execution runtime.**

## Why V35, and why not another guessed IDX format?

V31–V34 provide original-data scanning, real MT10 decoding, event evidence joins, and one **experimental original-Xbox Carbon IDX format**. But our original Undercover PS2 investigation through V21 included private Python code for IDX, CSI, EVT, SCHl and minibank construction. That earlier research code is still missing from the GitHub V22+ branch.

The original V21 ZIP is listed among this project's provided files. However, local Python and container execution is currently failing when the project ZIP is accessed. Uploading the copyrighted game source banks to public GitHub to work around this would be inappropriate.

**V35 makes recovery of the prior source practical on a working local computer**, without attempting to parse undocumented original game formats by guessing, or introducing more synthetic sound recordings.

## Tool: source-only archive recovery

[V35 Python tool](../tools/legacy_audio_research_recovery_v35.py) reads a private legacy research ZIP and identifies source/text entries with these extensions: `.py`, `.bms`, `.md`, `.rst` and `.txt`. It computes the ZIP SHA-256 and each selected file's SHA-256, plus filename and source-text topic flags for IDX, EVT, CSI, SCHl, MT10, SCDl, speech, group, and police.

**Inspect first, without extracting anything:**

    python audio/tools/legacy_audio_research_recovery_v35.py inspect --archive "D:\NFS_AUDIO_LAB\NFS_Undercover_Carbon_PC_Police_Audio_Research_V21.zip"

The path above is an **example location** on your own PC, not a verified location in the user's Windows installation.

**If the manifest contains the missing parser tools, extract the source files privately:**

    python audio/tools/legacy_audio_research_recovery_v35.py recover --archive "D:\NFS_AUDIO_LAB\NFS_Undercover_Carbon_PC_Police_Audio_Research_V21.zip" --out-dir "D:\NFS_AUDIO_LAB\v35_recovered_source"

The destination folder must **not exist**; it will contain `manifest.json` and a `research_sources/` tree with original relative paths. It never executes recovered code. It does not automatically copy anything to GitHub or modify any game installation.

## Security and privacy limits

- Full ZIP input capped at 64 MiB, each selected source member at 4 MiB, total selected text at 48 MiB, and 4,000 ZIP members maximum.
- Rejects absolute/traversal paths, Windows drive/ADS names, backslash paths, unusual ZIP file types including symlinks, encrypted entries, case-colliding ZIP names, oversized members, excessive compression ratios and corrupt ZIP files.
- Source-only extension filtering excludes original `.ASF`, `.WAV`, `.BIG`, `.IDX`, `.EVT` and `.CSI` binary assets. Text masquerading as binary or with invalid UTF-8 is skipped.
- Source files may themselves contain quoted private metadata or encoded samples. **Review recovered text before considering a selective public source-code migration.** Do not publish the original full research ZIP or its contents indiscriminately.
- Does not validate/execute source parsers recovered from the ZIP and does not independently confirm the authenticity of the ZIP's game-specific claims.

## Verified synthetic test

    python audio/tools/legacy_audio_research_recovery_v35.py self-test

This creates a small original, copyright-free synthetic ZIP containing a Python IDX parser, an EVT/CSI Markdown note and a fake ASF sound. The real V35 recovery code finds and restores only the code and text. The fake ASF is excluded. All recovered files are inspected/hashed, never executed.

**GitHub Actions evidence:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41217606419

**Automated suite:** 263/263 unit tests passed, including **31 new ZIP privacy/structure/security tests**, alongside separate official upstream vgmstream decoder checks from V24–V34 and the V35 source recovery self-test.

## V34 format caveat reaffirmed

The public [ResHax Black Box IDX/BIG extraction recipe](https://reshax.com/topic/160-help-extract-big-file-nfs-carbon-xbox-version/) was tested with **Carbon on the original Xbox**, not Undercover PS2. Do not treat the V34 0x54/count/16-byte-profile as proven PS2 fact, and do not substitute the opaque IDX ID for an original CSI/EVT event or group ID.

The point of recovering our V21 tools is to inspect the **actual prior Undercover PS2 parser and byte-level evidence**. If that native structure contradicts the Xbox profile, prefer the source-specific evidence and update the parser, rather than modifying checks to force the Xbox interpretation.

## What remains unfinished

- Actual private V21 source archive inspection and retrieval in this runtime. V35 was verified on copyright-free synthetic ZIP fixtures only.
- Import of the verified V19–V21 tools and authentic IDX/CSI/EVT parsers from that archive into the new GitHub audio branch.
- Genuine original Undercover police dialogue decoding, labeling, and original vs PC-style PCM comparison.
- Proof of Carbon PC's own sound bank loading, event routing or audible police-radio playback.

**Next milestone:** run V35 privately against the original V21 research ZIP, inspect its manifest for IDX/CSI/EVT source files, review/migrate only necessary code, and derive real event joins from documented source parsing rather than assumptions.