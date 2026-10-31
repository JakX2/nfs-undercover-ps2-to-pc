# V26: Verified PS2-v3 vs PC-v2 EA SCHl audio decoding

**Verified in GitHub Actions using an official upstream vgmstream CLI build.**

V26 is the first integration test in this branch invoking vgmstream's actual **EA SCHl block parser** instead of its generic TXTH reader. No copyrighted game audio is used.

## Synthetic experiment

The [V26 integration source](../tools/ea_schl_platform_pcm_selftest_v26.py) creates a deterministic 22,050 Hz mono PCM16LE signal and embeds it twice in independent EA SCHl containers. The two files share **exactly the same SCCl, SCDl and SCEl bytes**.

| Attribute | Original-style PS2 | PC-style |
| --- | ---: | ---: |
| Platform ID | 5 (PS2) | 0 (PC) |
| EA header version | 3 | 2 |
| SCHl header size | 36 bytes | 32 bytes |
| Codec2 | 0 (PCM16LE interleaved) | 0 (PCM16LE interleaved) |
| Sample rate | 22,050 Hz | 22,050 Hz |
| Channels | 1 | 1 |
| Data blocks | 2 x 2,048 frames | Identical original bytes |
| Total audio frames | 4,096 | 4,096 |

The test constructs variable header patches corresponding to version (0x80), channels (0x82), sample rate (0x84), total samples (0x85), and codec2 (0xA0). An optional priority patch is present only in the PS2 version to ensure different header lengths.

The V25 auditor validates that all post-header bytes are exactly identical. Then a **real official vgmstream-cli** performs metadata reading and WAV decoding on each EA stream, and the independent V22 PCM verifier checks both outputs against the original generated PCM.

## Verified results

The upstream decoder reports for both streams:
- Encoding: 16-bit PCM (block)
- Layout: blocked (EA SCHl)
- Metadata from: Electronic Arts SCHl header (variable)
- Sample rate: 22,050 Hz
- Channels: 1
- Total samples: 4,096

Original generated PCM SHA-256:

    7dcb5f3e116b41e6f08e5fb5b9a75d5e98b84fa566dbafaff6f643d506c7809d

Both decoded PCM payloads matched that exact hash.

**Verified decoder and CI job:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41209302225

## Reproduce

Install the upstream static vgmstream CLI from https://github.com/vgmstream/vgmstream-releases/releases/tag/nightly.

Run from the repository root:

    python3 audio/tools/ea_schl_platform_pcm_selftest_v26.py --decoder /path/to/vgmstream-cli

The test prints a JSON report of decoder metadata and source PCM hashes, and deletes its generated inputs and WAVs automatically.

To run the complete synthetic regression suite:

    python3 -m unittest discover -s audio/tests -p "test_*.py" -v

## Limits: genuine MT10 and Carbon runtime are not verified

**V26 does not decode genuine Undercover EA-MT10 speech.** EA codec2 value 0 in this experiment is uncompressed PCM16LE; Undercover compressed voice is EA MicroTalk MT10, codec2 value 4. The test verifies common SCHl container headers and block layout, not the speech codec's compressed bitstream.

It also does not establish that Carbon PC's runtime accepts a 22,050 Hz compressed voice stream, that IDX/BIG banks can be loaded, or that CSI/EVT police dialogue routing works.

Next gate: extract exactly one Undercover native SCHl clip and its corresponding V20/V21 experimental PC-shaped counterpart locally. Verify them with V25 and the real decoder on genuine EA-MT10 content. Keep recordings, WAVs and rebuilt banks out of the GitHub repository.
