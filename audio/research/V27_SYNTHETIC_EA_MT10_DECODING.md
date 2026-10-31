# V27: Real EA-MT10 decoder tested with independently generated compressed audio

**Verified in GitHub Actions:** The official upstream vgmstream CLI decoded two original synthetic MicroTalk compressed frames in both PS2-style and PC-style EA SCHl containers, with exact PCM equality for each pair.

**Important:** The test frames are copyright-free, independently generated codec fixtures, **not original Undercover game audio**. This establishes that the upstream decoder can decode MT10 under both tested wrappers, **not** that Carbon PC can play Undercover voices.

## Advance since V26

V26 tested the actual EA SCHl container parser but only decoded uncompressed PCM16 (EA codec2=0).

V27 uses **real MicroTalk compression (EA codec2=4)**. Its synthetic encoder writes a minimal controlled 48-byte compressed frame using the LSB-first grammar in upstream [utkdec.c](https://github.com/vgmstream/vgmstream/blob/master/src/coding/libs/utkdec.c).

Both frames are decoded by the actual official vgmstream MicroTalk decoder, which reports:

- Encoding: Electronic Arts MicroTalk
- Layout: blocked (EA SCHl)
- Sample rate: 22,050 Hz
- Channels: 1
- Total samples: 432

## Two independently decoded experiments

| Property | Silence | Nonzero RELP pulse |
| --- | --- | --- |
| Compressed frame | 48 bytes | 48 bytes |
| EA codec2 ID | 4 (EA-MT10) | 4 (EA-MT10) |
| PS2 wrapper | Platform 5, version 3 | Platform 5, version 3 |
| PC wrapper | Platform 0, version 2 | Platform 0, version 2 |
| Audio blocks across both wrappers | Byte-identical | Byte-identical |
| Upstream MicroTalk decoder succeeded | Yes | Yes |
| PCM equal between PS2 and PC | Yes | Yes |
| Decoded audio | Exactly 432 zeros | 432 frames including a nonzero signal |

The silence bitstream uses reduced-bandwidth RELP, reflection coefficients at the zero entry of MicroTalk's coefficient table, and zero excitation.

The second frame inserts one synthetic positive excitation pulse. The decoded audio is **non-silent** and still exactly equal across platform headers. This rules out a success that only occurs for silence.

### Observed PCM16 SHA-256

Silence:

    0ed9e26c3f1435e498beb2369bdf5a04a7fe4f0e302068ef2c308e1ff872b5f7

Nonzero pulse:

    5e829ae0c6da95f12655486aa1dc03d633d70e3328343a0a16adc7620b434034

The V25 SCHl auditor and V22 PCM comparator independently check block identity and decoder output.

**Verified CI run:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41210050997

**Regression tests:** 82/82 synthetic tests passed on the first extended V27 suite.

## Reproduction

Install the official upstream Linux or Windows vgmstream CLI from https://github.com/vgmstream/vgmstream-releases/releases/tag/nightly.

From the repository root:

    python3 audio/tools/ea_mt10_synthetic_silence_v27.py --decoder /path/to/vgmstream-cli
    python3 audio/tools/ea_mt10_synthetic_silence_v27.py --decoder /path/to/vgmstream-cli --pulse

The test creates temporary compressed streams and WAVs, verifies them, prints JSON without media, then deletes the temporary media. No original game files are required.

Source code:
- [V27 test generator](../tools/ea_mt10_synthetic_silence_v27.py)
- [V27 synthetic tests](../tests/test_ea_mt10_synthetic_v27.py)
- [V25 private comparison tool](../tools/schl_wrapper_audit_v25.py)

## Next gate: one real Undercover police recording

Use the privately held V19/V20/V21 extraction and PC-header reconstruction scripts with an original user-owned Undercover PS2 archive. Generate a matching original SCHl clip and experimental PC-shaped SCHl clip.

Then compare their actual compressed block identity and decoded PCM:

    python3 audio/tools/schl_wrapper_audit_v25.py --original /private/uc_original.asf --experimental /private/uc_pc_style.asf --decoder /path/to/vgmstream-cli --report /private/real_uc_pair_report.json

The ZIP-based earlier V1–V21 research sources have not all been migrated into GitHub, and no user-owned audio was available for this environment's actual-decoding experiment.

**Never publish game recordings, decoded original WAVs or proprietary reconstructed banks.**

## Unverified even after V27

- Actual Undercover EA-MT10 recording decoded and identified by listening
- Original-versus-PC-shaped decoded PCM equivalence for a real Undercover voice
- Carbon PC's own runtime acceptance of 22,050 Hz EA-MT10 at PC-style version 2
- Engine-integrated police IDX/BIG and verified CSI/EVT routing
- Original police radio playback in-game

The decoder's success does not imply Carbon PC engine compatibility. Keep the live game installation untouched.
