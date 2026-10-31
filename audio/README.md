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


## V24: decoder PCM round-trip from self-generated audio

[V24's real-vgmstream self-test](tools/vgmstream_real_decoder_selftest_v24.py) generates 4096 samples of original mono PCM16LE at 22,050 Hz, provides a TXTH description and makes the **official upstream CLI actually decode** it. It independently verifies that WAV PCM is byte-identical to the generated source, and a one-bit sample mutation survives decoding.

**Verified successful GitHub Actions run:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41207703967. See [evidence and private source-clip test instructions](research/V24_REAL_DECODER_SYNTHETIC.md) and [V24 regression tests](tests/test_real_decoder_selftest_v24.py).

**Important:** PCM16LE is an intentionally simple synthetic decoder test format, **not** Undercover EA-MT10; we have still not decoded a real Undercover police line or tested Carbon PC audio playback. Game recordings are never uploaded.


## V25: strict SCHl wrapper preservation audit

The [V25 verifier](tools/schl_wrapper_audit_v25.py) compares **two individual user-supplied SCHl recordings** and checks chunk sizes, SCCl/SCDl counts, post-header byte identity and per-block SHA-256 hashes. It handles the case where the original PS2 SCHl header and the experimental PC-style SCHl header have different lengths, without changing or redistributing any original audio.

An optional --decoder argument invokes the **real installed vgmstream-cli** and V22's sample-accurate PCM comparator on the same two files, using temporary WAVs that are removed afterwards. Unlike earlier experiments, the structural and decoded checks can now be requested together and reported in a single JSON audit.

**Verified synthetic suite:** 58/58 tests passed, plus the official upstream vgmstream PCM16LE/TXTH job in [GitHub Actions](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41208600250). See [V25 details and local usage](research/V25_SCHL_WRAPPER_AUDIT.md).

**Not yet verified:** real Undercover EA-MT10 PCM decoding, V20/V21 PS2-to-PC wrapper PCM equality, or Carbon PC playback. No copyrighted game audio is in the repository.


## V26: actual EA SCHl cross-platform header decoder test

[V26](tools/ea_schl_platform_pcm_selftest_v26.py) runs the actual **EA SCHl decoder**, not just the TXTH reader, on two synthetic EA sound streams with **identical compressed-block positions and original PCM samples**. The PS2-like container uses platform 5/version 3 and a 36-byte SCHl header; the PC-like container uses platform 0/version 2 and a 32-byte header. Both are decoded by the official vgmstream CLI to the same exact original 4,096-frame, 22,050 Hz PCM data.

This is an important verified **EA container compatibility** result in the upstream decoder, but it is **not an EA-MT10 codec test**. V26 uses uncompressed EA codec2=0, while real Undercover MicroTalk speech uses codec2=4.

See [V26 research report](research/V26_EA_SCHL_CROSS_PLATFORM.md) and [V26 regression tests](tests/test_ea_schl_platform_v26.py). No game audio or proprietary files were used or uploaded.


## V27: Real EA-MT10 compressed decoding with synthetic speech frames

V27 is the first verified experiment in this branch to exercise **vgmstream's EA MicroTalk compressed codec**, not merely its WAV/TXTH or EA SCHl uncompressed PCM pathways.

The [V27 source](tools/ea_mt10_synthetic_silence_v27.py) independently generates two copyright-free compressed 48-byte MicroTalk frames: exact silence and a nonzero positive RELP excitation pulse. Each frame is placed into a PS2-style EA SCHl version 3 wrapper and a PC-style version 2 wrapper, with audio blocks unchanged between them.

**Observed in official vgmstream CLI:** Both variants decode to exactly identical 432-frame, 22,050 Hz PCM. The silence frame produces only zeros; the second produces a verified nonzero signal. Upstream identifies both as Electronic Arts MicroTalk, codec2=4.

The [research notes](research/V27_SYNTHETIC_EA_MT10_DECODING.md) provide hashes, commands, GitHub Actions evidence and the next private genuine-voice test. The [V27 synthetic regression tests](tests/test_ea_mt10_synthetic_v27.py) are included.

**Limit:** This proves a MicroTalk codec pathway through the *upstream decoder*, **not original Undercover dialogue or Carbon PC runtime playback**. The original game audio archives remain private and were not uploaded.

## V28: One-command private MicroTalk rewrapper and decoded-PCM gate

The [V28 private converter](tools/undercover_mt10_private_bridge_v28.py) directly accepts **one privately extracted Undercover PS2 mono MicroTalk SCHl voice** and constructs an experimental PC platform 0/version 2 header, without requiring a Carbon reference stream. It retains all SCCl/SCDl/SCEl bytes unchanged, verifies compressed block identity with V25 and, when an official vgmstream CLI is supplied, compares the actual decoded PCM with V22.

The command writes a new private JSON report folder, discarding temporary experimental ASF and WAV by default. The user can explicitly retain the experimental ASF locally, but should not install it in Carbon PC yet.

**Verified CI:** 102/102 synthetic regression tests passed and the upstream decoder confirmed exact PCM identity for both generated synthetic MT10 silence and nonzero pulse after the V28 rewrapper. [GitHub Actions evidence](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41210582210).

See the [V28 private test instructions](research/V28_PRIVATE_MT10_ONE_COMMAND.md). This is a lab-only conversion tool. **Real Undercover dialogue still has not been decoded and verified**, and Carbon PC's sound engine, bank loading and event routing remain untested.
