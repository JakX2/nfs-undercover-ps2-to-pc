# Sound and music research

This directory tracks the **NFS Undercover PS2/Wii → Carbon PC** audio-research branch. Source-only research: no copyrighted game recordings or proprietary game files.

## Verified offline work through V21

- Original Undercover soundtrack replacement in Carbon PC: **reported working by the project owner**.
- GIN engine sweeps: common Ginsu2 structures across the supplied datasets. Undercover/Carbon console recordings share many byte-identical files.
- Police event catalogs: 242 Undercover events and 268 Carbon events, with candidate group references and platform-dependent event IDs.
- Police IDX/BIG: nested SCHl streams, indexing, audio stream boundaries and recording metadata are structurally parsed.
- EA-MT10 police speech: 22,050 Hz in supplied Undercover PS2/Wii datasets, 24,000 Hz in Carbon PC. **Audible decoding has not been verified.**
- V16: collision-avoiding **experimental** group-ID plan, scoped to the inspected police data.
- V18: lossless PS2/Wii wrapper transformation for 11,383/11,385 matched streams, with all 11,385 reversible.
- V20: SCHl/SCDl/SCCl block count and sample-count bookkeeping validated.
- V21: rebuilt **laboratory-only** IDX/BIG group fixtures with PC-style headers and original compressed audio. Tested: groups 292 and 300, 156 streams total, source compressed bytes preserved.

### V21 fixture statistics

| UC source group | Experimental ID | Clips | IDX | BIG |
| --- | ---: | ---: | ---: | ---: |
| 292 | 1067 | 12 | 232 bytes | 282,112 bytes |
| 300 | 1074 | 144 | 940 bytes | 2,862,592 bytes |

These are **offline structural results**, not in-game compatibility proof. V21 checks reported 28/28 passing tests with the original data available.

## Known blockers

1. Decode an actual Undercover EA-MT10 stream to PCM with a suitable decoder (for example vgmstream), listen, and verify PCM.
2. Confirm whether Carbon PC's EA-MT10 playback accepts PC-format headers paired with untouched Undercover 22,050 Hz blocks.
3. Map event commands to their exact voice recording selections; current group matches are candidates, not definitive routing.
4. Produce an engine-accepted full audio resource, with globally safe identifiers and correctly referenced IDX/BIG/CSI/EVT data.
5. Perform a reversible **single-event** runtime playback test.

## Safety and rights

Do not publish game assets or audio recordings here. Do not install experimental IDX/BIG files directly into Carbon PC. Keep source archives and reconstructed banks in a private local workspace.

## Research provenance

Compiled from the project's V6–V21 archive comparisons and V21 README. The earlier two uploaded PS2 SOUND archives had identical binary contents; their Undercover identity is **inferred** from cross-comparison with Wii data, not independently proven from disc metadata.

## V22: audio decode equivalence harness

The [V22 PCM equivalence tool](tools/ea_mt10_pcm_equivalence_v22.py), [synthetic tests](tests/test_pcm_equivalence_v22.py), and [usage/research notes](research/V22_DECODER_VALIDATION.md) live in this dedicated audio research branch.

- Compares original Undercover PS2 SCHl recordings against corresponding V20/V21 experimental PC-style SCHl recordings **only after an external official decoder provides real PCM WAV files**.
- SHA-256 verification compares **decoded PCM bytes**, sample rates, channel counts and total frames.
- Does not transcode EA-MT10, make a Carbon-installable bank, or validate playback inside the game.
- A GitHub Actions job runs standard-library synthetic tests without any extracted game assets.
- Earlier V1–V21 source archives remain available separately and **have not all been migrated** into this repository.


## V23: official decoder availability + metadata preflight

The [V23 vgmstream metadata-only probe](tools/vgmstream_metadata_preflight_v23.py) reads the **actual decoder's** sample rate, channel count, sample count, and encoding for one original SCHl stream and its PC-shaped counterpart. It never generates audio or modifies original streams. The [V23 documentation](research/V23_DECODER_PREFLIGHT.md) gives the private local commands; the [synthetic tests](tests/test_metadata_preflight_v23.py) exercise parsing and safety behavior.

**Verified GitHub Actions:** 32/32 synthetic tests passed, and the official Linux vgmstream CLI downloaded and launched successfully in the separate smoke-test job. [Successful run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41206998993).

**Still unverified:** genuine Undercover EA-MT10 voice decoding, original-vs-PC-style PCM identity, an encoder for Carbon PC speech, or in-game police-voice playback. Neither V22 nor V23 can be used to install a playable voice bank.
