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

## V29: MT10 compressed audio across multiple SCDl blocks

The [V29 real-decoder experiment](tools/ea_mt10_multiblock_continuity_v29.py) uses three independently generated MicroTalk blocks in the same EA SCHl recording. Only the first block includes codec initialization, while later blocks continue the codec state. A middle-block nonzero pulse is preserved through the actual V28 PS2-to-PC experimental header rewrapper and decoded by the real upstream vgmstream decoder.

**Verified:** 1,296 samples at 22,050 Hz, three compressed SCDl blocks, exact PS2/PC-wrapper PCM identity, and an intentionally altered middle-block negative control that changes the decoded audio. The expanded [118/118 synthetic test suite and real decoder job passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41211334656).

See the [V29 research and reproduction notes](research/V29_MT10_MULTIBLOCK_CONTINUITY.md) and [V29 regression tests](tests/test_ea_mt10_multiblock_v29.py). All fixtures are copyright-free and generated from scratch. The genuine Undercover police voices and Carbon PC's in-game audio engine **remain untested** in this V29 run.

## V30: Multiple MicroTalk frames inside one SCDl

[V30](tools/ea_mt10_multiframe_scdl_v30.py) verifies the actual upstream MicroTalk decoder against **three originally generated MT10 compressed frames inside a single EA SCDl audio block**. This is different from V29, where the same sequence occupied three independent SCDl blocks.

**Verified:** The V28 PS2/v3-to-PC/v2 header operation preserves every original compressed byte; the actual upstream decoder produces exactly equal PCM for both headers, and the **same PCM also comes out when the frames are distributed across three SCDl blocks**. An intentionally removed middle-frame excitation changes decoded audio.

The expanded synthetic suite passed **134/134** tests and the upstream real-decoder integration check passed. See the [V30 research report](research/V30_MT10_MULTIFRAME_SINGLE_BLOCK.md) and [V30 synthetic tests](tests/test_ea_mt10_multiframe_scdl_v30.py).

**Still unverified:** An actual Undercover police recording, complete bank loading/event routing, Carbon PC engine support or audible in-game voices. No original game assets are included in GitHub.

## V31: Private BIG voice scanner with mandatory real decoded-PCM verification

The [V31 BIG scanner](tools/undercover_big_voice_scan_v31.py) bridges the gap between extracted local original PS2 .BIG sound banks and the V28 decoder/PC-style-header experiment. It searches **read-only** for contiguous mono PS2 platform5/v3 EA-MT10 SCHl streams, validates chunk boundaries, SCCl/SCDl sample accounting and source headers, then reports candidate offsets without exporting any proprietary audio.

The separate **verify** command selects one of those offsets, privately extracts the original SCHl into a temporary folder, invokes V28, and **requires the real upstream vgmstream CLI** to confirm exact PCM identity against the experimental PC-style header. Only a new metadata JSON report is retained by default; original and reconstructed audio are deleted. False positives, malformed streams, invalid offsets and decoder failures are rejected.

**Verified:** 162/162 synthetic regression tests passed. The official upstream decoder independently validated two generated mono MT10 streams located inside a mock BIG, with identical PCM after the experimental wrapper operation. See the [successful GitHub Actions run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41212591848) and the [V31 private usage guide](research/V31_PRIVATE_BIG_VOICE_SCANNER.md).

**Still unverified:** The original Undercover PS2 archives have not been scanned or decoded with V31 in this environment, and SCHl signature discovery alone cannot prove a stream is police dialogue. Carbon PC's actual bank loader, event mapping and runtime playback are not tested. The original game archives and extracted audio must stay out of this public repository.

## V32: Batch offline decoding of candidate MicroTalk voices

The [V32 private batch triage](tools/big_mt10_batch_triage_v32.py) builds on V31. It scans an extracted local PS2 BIG for mono EA-MT10 SCHl candidates and runs an **independent upstream vgmstream decoded-PCM comparison** on a limited batch, applying V28's experimental PC/v2 header rewrap privately. It outputs a new **metadata-only JSON** report that separates successful PCM equality from actual decoder/validation failures and never keeps original audio or WAVs.

**Verified:** 182/182 synthetic Python tests passed. The real official decoder then successfully validated both synthetic MT10 BIG recordings in the V32 end-to-end batch self-test, preserving identical PCM across different SCDl packing. [Successful GitHub Actions run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41213209246).

See the [V32 local testing instructions](research/V32_PRIVATE_BATCH_MT10_TRIAGE.md) and [V32 regression tests](tests/test_big_mt10_batch_triage_v32.py).

**Outstanding:** We have still not decoded real Undercover police speech in this environment. V32 cannot identify police event IDs from SCHl scans alone. Actual IDX/CSI/EVT association, Carbon PC bank loading and in-game playback remain unverified.

## V33: IDX → EVT → CSI evidence join for identified audio candidates

The [V33 evidence joiner](tools/idx_evt_csi_evidence_join_v33.py) adds **explicit source event attribution** to V31's scanned SCHl offsets, with optional V32 real decoded-PCM results. It joins **operator-exported CSVs** for IDX (group/substream → BIG offset/length), EVT (event → group), and CSI (event ID → event name/classification) and cross-checks declared source lengths. Offset-only associations, conflicting lengths, multiple events, and IDX aliases are reported rather than silently treated as confirmed voice identities.

**Verified:** 209/209 synthetic Python regression tests passed and the separate official vgmstream decoder job passed. See [V33 research and CSV schema](research/V33_IDX_EVT_CSI_EVIDENCE_JOIN.md) and [GitHub Actions evidence](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41215619199).

**Important limitation:** V33 does not parse original binary IDX, EVT or CSI by itself. It needs authentic CSV exports from the earlier local research. A CSI `police` classification is an operator label, **not** a confirmed audible police recording. Actual Undercover voice decoding and Carbon PC sound bank/event playback remain unverified.

## V34: Source-grounded native IDX offset-table hypothesis

An independently documented [Black Box IDX/BIG extraction recipe](https://reshax.com/topic/160-help-extract-big-file-nfs-carbon-xbox-version/) for **Carbon original Xbox** describes a 32-bit record count at IDX byte offset `0x54` and 16-byte records with three opaque integer fields plus an offset into BIG. The new [V34 native IDX auditor](tools/experimental_native_idx_audit_v34.py) implements that **as an experimental profile**, with strict count, endian, increasing-offset, BIG-span and original SCHl boundary checks. The opaque `raw_id` is **not** assigned a guessed CSI/EVT group identity.

**Verified synthetic experiment:** 232/232 automated Python regressions passed, plus an upstream vgmstream real-decoder test that joined two originally generated IDX offsets to valid compressed MicroTalk audio in BIG, including one padded stream span. Both original-versus-experimental-PC decoded PCM pairs matched. See [V34 research notes](research/V34_NATIVE_IDX_OFFSET_HYPOTHESIS.md) and the [successful CI run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41216490127).

**Important:** V34 has **not** verified the IDX profile on original Undercover PS2 IDX/BIG files. The source recipe came from Carbon **Xbox**, and the original game archive is still inaccessible to the local execution environment. A real IDX/EVT/CSI police-event identity and Carbon PC sound playback remain unproven.

## V35: Recover original V1–V21 research source code safely

The [V35 legacy source recovery tool](tools/legacy_audio_research_recovery_v35.py) provides a conservative offline path to inspect and privately recover the missing original **V21 police-audio research scripts** from a user-owned ZIP archive. It accepts only Python, QuickBMS and selected text/documentation extensions by default, preserves original file hashes, identifies likely IDX/CSI/EVT/SCHl/MT10 parsers, rejects unsafe ZIP structures, and **never executes extracted source** or automatically publishes it.

**Verified:** 263/263 synthetic Python tests passed, including 31 new source recovery, ZIP security, binary filtering, metadata and no-overwrite cases. The separate upstream decoder integration and V35 source-only self-test also passed. See the [V35 recovery instructions](research/V35_RECOVER_LEGACY_AUDIO_SOURCES.md) and [verified CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41217606419).

**Limit:** The actual private V21 ZIP was registered in this Project but not readable through the local Python/container environment during V35. No original source parsers were recovered or committed, no original police recording was decoded, and Carbon PC runtime playback remains unverified. The V34 Xbox IDX profile is still an unproven hypothesis for Undercover PS2.

## V36: Discover candidate native IDX record layouts from verified SCHl offsets

The [V36 IDX layout discovery tool](tools/native_idx_layout_discovery_v36.py) avoids assuming that Carbon Xbox's published IDX format applies to Undercover PS2. It searches bounded alternative count positions, table starts, row widths, offset-word positions and byte orders, then checks each hypothesis against **independently validated SCHl offsets from a matching V31 scan**. It ranks candidates but never declares a native layout, CSI/EVT mapping or police audio event proven.

**Verified synthetic testing:** 291/291 Python regressions and the separate official vgmstream CLI integration passed. V36's own self-test recovers two different artificial IDX layouts and also uses the **real V31 SCHl scanner** to verify offsets in a generated MicroTalk BIG. See [V36 instructions and assumptions](research/V36_IDX_LAYOUT_DISCOVERY.md) and [the latest audio CI runs](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions).

**Remaining original-data gate:** Test V36 against the actual Undercover PS2 IDX/BIG pair and reconcile any candidate format with the user's original V21 parser. Neither the Xbox format nor the V36 search outcome has been verified against original Undercover file bytes. No real police recording or Carbon PC in-game speech has been decoded or played.
