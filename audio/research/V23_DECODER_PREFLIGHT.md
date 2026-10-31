# V23: Official vgmstream CLI smoke test + real-stream metadata preflight

**Status (2026-10-31):** GitHub Actions run **41206998993** succeeded. Two jobs passed: the V22/V23 synthetic tests and the official static Linux decoder download/startup check. These jobs include **no original game recordings**; this is not evidence that an Undercover voice decoded, nor that Carbon PC can play the experimental bank.

## What V23 actually adds

- An independent GitHub Actions check that downloads the **official nightly static Linux vgmstream CLI**, records the compressed archive SHA-256, extracts the executable, and checks that it starts and prints help.
- [Metadata preflight tool](../tools/vgmstream_metadata_preflight_v23.py) that runs vgmstream **metadata-only** mode (-m) on *two individual SCHl recordings*: the original Undercover PS2 stream and V20/V21's experimental PC-style copy.
- [16 new synthetic tests](../tests/test_metadata_preflight_v23.py), in addition to V22's 16 tests.
- JSON containing decoder SHA-256, source SHA-256 and sizes, sample rate, channels, sample count, and encoding. **No audio is decoded** by V23.

The official vgmstream tool documents the -m argument for metadata and -i with -o for single-play WAV decoding:

- https://github.com/vgmstream/vgmstream/blob/master/doc/USAGE.md
- https://github.com/vgmstream/vgmstream-releases/releases/tag/nightly

## Privately test real clips

Use the **separate local V19/V20/V21 tools** to extract one Undercover PS2 clip and its *corresponding* PC-shaped wrapper. Both inputs must be **individual SCHl streams**, not IDX or BIG containers.

Windows PowerShell (adjust paths):

~~~powershell
python audio/tools/vgmstream_metadata_preflight_v23.py --original "D:\NFS_Audio_LAB\uc_original.asf" --experimental "D:\NFS_Audio_LAB\uc_pc_style.asf" --decoder "D:\Tools\vgmstream\vgmstream-cli.exe" --report "D:\NFS_Audio_LAB\metadata_v23.json"
~~~

Linux:

~~~bash
python3 audio/tools/vgmstream_metadata_preflight_v23.py \
  --original /private/uc_original.asf \
  --experimental /private/uc_pc_style.asf \
  --decoder /tools/vgmstream-cli \
  --report /private/metadata_v23.json
~~~

**The report path must not already exist.** Original and experimental paths must differ. The tool never overwrites either source and invokes only vgmstream -m, producing no WAVs.

A successful metadata preflight compares four decoder-reported attributes:

- Sample rate: original Undercover compressed streams are ordinarily **22,050 Hz**
- Channel count
- Stream sample count
- Decoder encoding label

Exit codes: 0 when all four agree; 1 for mismatch; 2 if the decoder/source is invalid, metadata is incomplete, or the report path is unsafe.

**Passing metadata does not prove a lossless audio conversion.** If both parse, run the V22 PCM comparator **privately**:

~~~bash
python3 audio/tools/ea_mt10_pcm_equivalence_v22.py decode-pair \
  --original /private/uc_original.asf \
  --experimental /private/uc_pc_style.asf \
  --decoder /tools/vgmstream-cli \
  --out-dir /private/v22-new-result
~~~

V22 returns exact_pcm_match=true only if PCM16 bytes and audio parameters match. The output directory must be new; WAVs are removed by default. Keep all original and decoded game audio out of GitHub.

## Tests and CI

~~~bash
python -m unittest discover -s audio/tests -p "test_*.py" -v
~~~

**Observed:** 32 synthetic tests passed in GitHub Actions. The official CLI also started successfully on the Ubuntu runner, using the upstream nightly binary. That nightly may change, so the workflow records its compressed archive SHA-256. No fixed release checksum is currently pinned.

Verified run: https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41206998993

## Next experimental gate

We have a runnable decoder inside GitHub Actions, but **no game audio was fed to it**. Next: a real private metadata/decode-pair comparison on one Undercover clip and its PC-shaped counterpart. Only then can we separate stream-wrapper compatibility from Carbon PC's bank-loader and event-routing problems.

V23 does **not** create an MT10 encoder, re-encode 24 kHz speech, install files in Carbon, or prove runtime playback.
