# V24: End-to-end vgmstream decoder verification with generated audio

**Status:** First *real decoder executable* pipeline verified in GitHub Actions, **without any original game material**. This is stronger than V23's CLI startup check but does **not** establish EA-MT10 decoding or Carbon PC playback.

## Results

The [V24 integration tool](../tools/vgmstream_real_decoder_selftest_v24.py) creates two original, deterministic mono PCM16LE streams at 22,050 Hz, each **4096 sample frames**, in a temporary folder. The second stream differs from the first by exactly **one flipped bit in one sample**.

It writes a TXTH descriptor using vgmstream's documented headerless-audio specification and invokes the **real upstream vgmstream-cli**:

1. The CLI's metadata-only command (-m) reads each generated file, reports sample rate, channel count, codec and frame count.
2. The CLI's actual decoder (-i -o) converts the raw PCM16LE into WAV.
3. V22's WAV inspector hashes **the PCM payload**, rather than RIFF header bytes.
4. The script independently SHA-256 hashes each original raw PCM buffer.
5. Both decoded WAV PCM hashes must match the corresponding original raw PCM hashes exactly, and the two test streams must differ.

**Observed, verified GitHub Actions run:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41207703967

- Official Linux vgmstream CLI downloaded and executed successfully.
- Sample rate reported by decoder: 22,050 Hz
- Channels: 1
- Decoded sample frames: 4,096
- Actual decoded audio encoding: 16-bit little-endian PCM
- Original synthetic PCM SHA-256: f69b6dde81b6943bd11b1c4669eaf5798bb41efab6821152da4f057ff06a9674
- PCM round-trip bit-exact: **YES**
- One-bit mutation detected: **YES**
- Actual EA-MT10 speech decoded: **NO**
- Carbon PC engine tested: **NO**

The upstream nightly is mutable and the CI prints the downloaded archive SHA-256. These checks use synthetic PCM only; no original samples or proprietary formats are uploaded.

## Run the synthetic self-test locally

Obtain the official vgmstream-cli executable (for example from https://github.com/vgmstream/vgmstream-releases/releases/tag/nightly) and Python 3.11+.

From the repository root:

~~~bash
python audio/tools/vgmstream_real_decoder_selftest_v24.py --decoder /path/to/vgmstream-cli
~~~

On Windows:

~~~powershell
python audio/tools/vgmstream_real_decoder_selftest_v24.py --decoder "D:\Tools\vgmstream\vgmstream-cli.exe"
~~~

The script creates a temporary directory, tests and deletes its own generated WAVs/raw audio automatically, and prints a JSON report.

## Then test an actual original Undercover voice *privately*

1. From your **original locally owned** source archives, use the independent V19/V21 source extraction tools to obtain the matching native Undercover PS2 SCHl stream and the V20/V21 PC-shaped version. Keep the source clips local.
2. Use V23's metadata preflight on the two extracted individual streams, not the full BIG/IDX containers:
   
~~~bash
python audio/tools/vgmstream_metadata_preflight_v23.py --original /private/uc_original.asf --experimental /private/uc_pc_shape.asf --decoder /path/to/vgmstream-cli --report /private/metadata_v23.json
~~~

3. If both parse, use V22's exact PCM comparator:
   
~~~bash
python audio/tools/ea_mt10_pcm_equivalence_v22.py decode-pair --original /private/uc_original.asf --experimental /private/uc_pc_shape.asf --decoder /path/to/vgmstream-cli --out-dir /private/new-comparison
~~~

V22 reports the SHA-256 of the decoded PCM as well as the decoder and source hashes, and deletes WAVs by default. Do **not** commit or upload either source recording, the decoded WAVs, or the rebuilt bank.

## What remains unverified

- Does vgmstream decode an actual Undercover EA-MT10 police recording correctly?
- Does the experimental Carbon-shaped SCHl wrapper decode to identical PCM to its PS2 source?
- Does Carbon PC's own audio engine accept 22,050 Hz MT10 with a PC-shaped v2 header?
- Can an isolated IDX/BIG bank be loaded and selected from a correctly patched police CSI/EVT event?
- Does a controlled in-game pursuit play the original voice?

No V24 result establishes any of the above. A successful PCM equivalence test in vgmstream would still **not** imply in-game compatibility.

## References

- Official TXTH documentation: https://github.com/vgmstream/vgmstream/blob/master/doc/TXTH.md
- Official CLI documentation: https://github.com/vgmstream/vgmstream/blob/master/doc/USAGE.md
- V22 PCM comparator: ../tools/ea_mt10_pcm_equivalence_v22.py
- V23 metadata probe: ../tools/vgmstream_metadata_preflight_v23.py
