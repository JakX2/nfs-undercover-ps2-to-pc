# V30: Three compressed EA-MT10 frames inside ONE SCDl block

**Verified with the real official vgmstream CLI:** Synthetic MicroTalk frames decode identically under an original-style PS2 platform 5/version 3 EA SCHl header and the V28 experimental PC platform 0/version 2 header, with all compressed blocks unchanged.

This is a research-only decoder test. The frames are generated entirely by our own code, not extracted from Undercover; Carbon PC's proprietary audio engine has NOT been tested.

## Why V30 matters

V29 proved that vgmstream's EA MicroTalk codec continued across three separate SCDl audio blocks. A voice recording can also contain MULTIPLE MicroTalk frames inside one SCDl block. V30 tests this case with actual upstream decoding and a controlled negative sample.

## Test construction

- Reuses the same three generated MT10 frame bitstreams from V29: first silent frame, second with a nonzero RELP pulse, third silent.
- Only the first frame contains the global MicroTalk initialization bits.
- The silent continuation frame is 46 bytes, while the continuation with the pulse is 47 bytes due to the additional bit crossing the byte boundary.
- Packs all three compressed frames into ONE SCDl, with 1,296 samples declared in the block; SCCl declares exactly one block.
- Builds the original PS2/v3 SCHl using the same header profile as V29 and passes it into the unchanged V28 PC/v2 rewrapper.
- Independently compares the entire compressed body, checks EA codec identification, decodes both variants, verifies their PCM hashes, and confirms a synthetic no-pulse negative control changes the audio.
- **Also decodes the identical three-frame sequence in V29's three separate SCDl blocks and compares that PCM against V30's single-block packing.**

## Independently verified outcome

| Check | Result |
| --- | --- |
| Official vgmstream reports Electronic Arts MicroTalk | Pass |
| Compressed frames in one SCDl | 3 |
| Original sample count | 1,296 mono frames at 22,050 Hz |
| Original and experimental PC body bytes | Exactly identical |
| Original PS2 versus PC-style PCM | Exactly identical |
| One SCDl versus three SCDl layout PCM | Exactly identical |
| Middle frame has nonzero decoded signal | Yes |
| Negative control without middle pulse | Different PCM |

PCM16 SHA-256 (PS2 original, PC-style wrapper, and 3-SCDl reference all equal):

    4881991e5814b8e901efa85c44d4ab0c6c7b610b5ea8413b90c7c972b9ade1d6

Negative-control PCM16 SHA-256:

    b2069f33fd956c79679b2e5a25c60cd0eab63b023d12111ff0242ae50896e9e1

Original preserved compressed body SHA-256 for V30's single SCDl:

    cf519ef692ca4136c1d6430f100b2a60fe6c0c4d1b0851c60e1ac237c00cd986

**Decoder evidence:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41211743622

**Final expanded synthetic suite:** 134/134 tests passed and the official decoder job passed after correcting an initial test expectation about pulse-frame byte length. See https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41211812580

## Source and reproduction

- [V30 real decoder integration](../tools/ea_mt10_multiframe_scdl_v30.py)
- [16 V30 synthetic regression tests](../tests/test_ea_mt10_multiframe_scdl_v30.py)
- [V29 three-block comparison reference](../tools/ea_mt10_multiblock_continuity_v29.py)
- [V28 direct header converter](../tools/undercover_mt10_private_bridge_v28.py)

Install the upstream vgmstream CLI from https://github.com/vgmstream/vgmstream-releases/releases/tag/nightly and run from the repository root:

    python3 audio/tools/ea_mt10_multiframe_scdl_v30.py --decoder /path/to/vgmstream-cli

The test makes all of its synthetic recordings and decoded WAVs inside a private temporary directory, then removes them. Only metadata and hashes are printed. No game files are needed.

## Remaining gaps

- **No genuine Undercover police dialogue has been decoded** in this turn; the file-execution environment used to read earlier uploaded game archives is unavailable.
- This checks one and three SCDl blocks with three total frames. Actual voice blocks may include dozens of variable-length MT10 frames, stereo channels, or additional chunk/header variants.
- V30 does NOT prove Carbon PC itself accepts a V28 header, a rebuilt IDX/BIG bank, police CSI/EVT event routing, or actual pursuit audio playback.
- The original 22,050 Hz data is not transcoded or resampled to 24,000 Hz. No original copyrighted audio is distributed.

**Next gate:** Obtain one privately extracted original Undercover PS2 mono police SCHl, run V28 with an installed vgmstream CLI and publish only a sanitized comparison report. Only then investigate a reversible, isolated Carbon PC runtime test.