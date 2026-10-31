# V29: EA-MT10 codec continuity across multiple SCHl data blocks

**Status: independently verified using the official upstream vgmstream-cli.**

The V29 generator creates a copyright-free compressed Electronic Arts MicroTalk (EA-MT10, codec2=4) stream containing **three distinct SCDl blocks**. It then passes the entire original PS2/v3 SCHl stream through V28's actual PC/v2 header rewrapper and compares the decoded output of both variants using the real vgmstream codec.

**No commercial game audio is included.** This remains a synthetic decoder/container experiment, not a decoded Undercover dispatch recording and not proof of Carbon PC engine playback.

## Why V29 matters

V27 and V28 proved one independently generated compressed MicroTalk frame could decode under both EA platform headers. Actual Undercover speech streams contain multiple SCDl blocks. At these boundaries, the EA MT decoder must advance compressed-data pointers, continue its codec state and not incorrectly reparse its global setup fields.

V29 explicitly tests that behavior:

1. Generate a valid MT10 frame with the global MicroTalk initialization bits and silent excitation.
2. Generate a second MT10 frame with **no repeated global initialization** and a nonzero RELP excitation pulse.
3. Generate a third continued MT10 frame, again without a repeated codec header.
4. Put these frames in three independent SCDl chunks, one compressed frame per block, each declaring 432 samples.
5. Build the enclosing original-style PS2 platform 5/version 3 EA SCHl and SCCl count=3.
6. Convert the original PS2 file with V28's real PC platform 0/version 2 rewrapper, preserving every byte of the original audio body.
7. Use V25 to verify all blocks and post-header bytes are unchanged.
8. Invoke the **official real vgmstream-cli** to inspect and decode both versions, verifying the output sample count and exact PCM hash.
9. Run a negative control in which the second block has its pulse removed. That altered middle block must fail structural identity and produce a different decoded PCM hash.

## Verified numbers

| Property | Observed result |
| --- | --- |
| EA codec | Electronic Arts MicroTalk, codec2=4 |
| Audio blocks | 3 distinct SCDl |
| Total decoded samples | 1,296 mono |
| Sample rate | 22,050 Hz |
| Original PS2 SCHl header | 36 bytes |
| Experimental PC SCHl header | 36 bytes |
| First block decoded silent | Yes |
| Second block decoded nonzero | Yes |
| PS2 and PC-wrapped PCM hashes equal | Yes |
| Negative control yields different audio | Yes |

Original PS2 and experimental PC PCM SHA-256:

    4881991e5814b8e901efa85c44d4ab0c6c7b610b5ea8413b90c7c972b9ade1d6

Negative control (no middle pulse) PCM SHA-256:

    b2069f33fd956c79679b2e5a25c60cd0eab63b023d12111ff0242ae50896e9e1

Preserved original post-SCHl compressed body SHA-256:

    872344927d204b3e9f0c4b06b10c19a1b4ea3eb9de8f855f149fa4f064a348a4

**Verified real-decoder evidence:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41211257502

**Verified extended source-code tests:** 118/118 synthetic unit tests passed in https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41211334656. The official real decoder job also passed.

## Reproduce without any game recordings

Install the upstream vgmstream CLI from https://github.com/vgmstream/vgmstream-releases/releases/tag/nightly and run from the repository root:

    python audio/tools/ea_mt10_multiblock_continuity_v29.py --decoder /path/to/vgmstream-cli

The script creates its own synthetic compressed ASF and WAV files only in a private temporary directory and deletes them on exit. It prints metadata and hashes as JSON. The test does not require any copyrighted file or modify a game installation.

New code:
- [Multi-block codec experiment](../tools/ea_mt10_multiblock_continuity_v29.py)
- [16 V29 regression tests](../tests/test_ea_mt10_multiblock_v29.py)
- [V28 single-recording conversion path](../tools/undercover_mt10_private_bridge_v28.py)

## Remaining uncertainty

**The user's original Undercover PS2 sound archives appear in the project conversation, but the current file-execution environment is unavailable.** We therefore have NOT decoded any actual original Undercover police voice in V29.

The successful multiblock check only establishes compatibility with *vgmstream*, not Carbon PC's own proprietary sound engine. It also tests one compressed MT10 frame per SCDl block; original streams often contain multiple codec frames per block and include stereo variants. Those need separate testing. No 24,000 Hz conversion or native PC MT10 re-encoding was performed. CSI/EVT event routing and installation of an actual sound bank remain unverified.

**Next genuine-data gate:** Privately extract a known original Undercover PS2 mono SCHl stream and run the existing V28 one-command conversion with an installed vgmstream-cli. Preserve its decoded PCM report locally and share a metadata-only summary, never the copyrighted audio, on GitHub.