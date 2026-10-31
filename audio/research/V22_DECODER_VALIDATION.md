# V22: EA-MT10 decoded-PCM equivalence test

**Status:** New test harness committed for review. The original Undercover voice and the experimental Carbon PC-style stream **have not yet been decoded and compared**. V21 laboratory banks are not playable mods.

## Objective

V20 changed one isolated Undercover PS2 \`SCHl\` audio header to the shape seen in Carbon PC. V21 applied the idea to reconstructed \`IDX/BIG\` groups 292 (12 recordings) and 300 (144 recordings). Both experiments preserved Undercover's compressed audio, including its 22,050 Hz sample rate. Their *structural* parsing passed, but that does **not** prove a decoder produces the same sound from both streams.

V22 adds an independent [PCM comparison tool](../tools/ea_mt10_pcm_equivalence_v22.py), not a new codec encoder.

## Evidence and expected outcome

vgmstream's official EA SCHl parser includes the \`EA_CODEC2_MT10\` / MicroTalk decoder branch, and its CLI supports \`-i\` (ignore looping, play once), \`-o\` (WAV output), and \`-m\` (metadata-only). Links:

- https://github.com/vgmstream/vgmstream/blob/master/src/meta/ea_schl.c
- https://github.com/vgmstream/vgmstream/blob/master/cli/vgmstream_cli.c
- https://github.com/vgmstream/vgmstream/blob/master/doc/USAGE.md

**Test hypothesis:** Because the V20/V21 conversion preserves all compressed audio blocks, the original PS2 and PC-style streams should decode to **exactly equal, 22,050 Hz PCM** if vgmstream interprets both stream headers equivalently. This must be demonstrated, not assumed.

A matching PCM hash would validate a lossless transformation **in vgmstream only**, not Carbon PC's playback implementation or group routing.

## Inputs: use original game assets locally

1. Install the official \`vgmstream-cli\` for your OS; add its directory to \`PATH\` or pass the full executable path.
2. Extract an individual original Undercover PS2 \`SCHl\` stream (e.g. a group 292 recording) with \`voice_preview_v19.py extract\` from your **local** V19/V21 package.
3. Generate the corresponding PC-style \`SCHl\` copy via your **local** V20/V21 reconstruction tools, keeping the same source clip.
4. Verify both files begin with the four bytes \`SCHl\`. Do not use an \`IDX\` or \`BIG\` file as a direct CLI input.
5. Work outside your Carbon PC installation. Do not commit the original streams, extracted WAVs, or rebuilt banks.

## Command line

Windows PowerShell:

\`\`\`powershell
python audio/tools/ea_mt10_pcm_equivalence_v22.py decode-pair --original "D:\NFS_Audio_LAB\uc_original.asf" --experimental "D:\NFS_Audio_LAB\uc_pc_style.asf" --decoder "D:\Tools\vgmstream\vgmstream-cli.exe" --out-dir "D:\NFS_Audio_LAB\v22_result"
\`\`\`

Linux:

\`\`\`bash
python3 audio/tools/ea_mt10_pcm_equivalence_v22.py decode-pair \
  --original /path/to/uc_original.asf \
  --experimental /path/to/uc_pc_style.asf \
  --decoder /path/to/vgmstream-cli \
  --out-dir /path/to/new-v22-result
\`\`\`

The output directory must not exist already. The tool records source-stream SHA-256, decoder executable hash, format metadata, and independent 16-bit PCM hashes. By default, it removes the decoded WAVs after comparison. Use \`--keep-wavs\` for **local/private** listening.

If both recordings have already been decoded:

\`\`\`bash
python3 audio/tools/ea_mt10_pcm_equivalence_v22.py compare-wavs uc.wav uc_pc_style.wav
\`\`\`

This command does not invoke a decoder and can be used for workflow checks with synthetic PCM WAVs.

## Interpretation

| Outcome | Meaning |
| --- | --- |
| Exit 0; \`exact_pcm_match: true\` | Both PCM streams share sample rate, channels, number of frames, and exact PCM bytes. |
| Exit 1; \`exact_pcm_match: false\` | Format, duration, or decoded PCM differs; **investigate before moving toward runtime**. |
| Exit 2 | Missing decoder, missing source, unsupported output format, or an invalid/unsafe output path. |

Even successful V22 results **do not** establish 24 kHz MT10 encoding, Carbon PC runtime support, or correct CSI/EVT routing. Future work must test these independently.

## Tests and limitations

\`\`\`bash
python3 -m unittest discover -s audio/tests -p "test_*.py" -v
\`\`\`

The V22 tests generate their own small synthetic PCM WAVs and use a mock decoder for orchestration checks. They do **not** test EA-MT10 or actual copyrighted voices. CI success validates the harness, not the port.

The V1–V21 source ZIP archive has not yet been fully migrated into GitHub. V22 assumes the separate local V19/V20/V21 extraction and bank-building tools remain available. This document contains no original game asset.
