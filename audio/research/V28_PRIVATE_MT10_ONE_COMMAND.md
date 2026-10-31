# V28: Private one-command Undercover PS2 MT10 wrapper experiment

**Status:** Implemented and independently verified using two original generated EA-MT10 frames. The official vgmstream decoder confirmed exact PCM equality across PS2 v3 and PC v2 wrappers. **No original game recording was tested in V28.**

## What changed

The [V28 private converter](../tools/undercover_mt10_private_bridge_v28.py) works directly from an **individual PS2 SCHl voice stream**. It does not need a separate PC reference file or V20/V21 header-replacement script.

It performs offline checks before producing an experimental PC platform 0/version 2 header: PS2 platform 5/version 3, mono only, EA MicroTalk codec2=4, source sample rate (including implicit 22,050 Hz), and header sample count equal to the sum of SCDl audio block samples. Source bytes after the original SCHl header are preserved **byte-for-byte**. The independent V25 block auditor checks the result.

An optional installed official vgmstream-cli then decodes the original and experimental ASF privately, compares decoded PCM16 bytes, sample rate, frame count and channel count, and deletes temporary audio files. An output directory must be NEW; no existing user file is overwritten.

## Test on one real privately extracted mono Undercover voice

First extract **one individual SCHl stream** using the earlier private V19/V20/V21 archive scripts or an equivalent local extraction tool. Do not pass a whole IDX/BIG container.

Windows PowerShell, run from the repository root:

    python audio/tools/undercover_mt10_private_bridge_v28.py --original "D:\NFS_Audio_LAB\uc_original_mono.asf" --decoder "D:\Tools\vgmstream\vgmstream-cli.exe" --out-dir "D:\NFS_Audio_LAB\v28_first_real_test"

Default output is **report.json only** in a new private directory. The generated PC-shaped ASF and the decoded WAVs are temporary and deleted after comparison. Use the optional flag --keep-pc-shape to retain the PC-shaped ASF privately for additional offline inspection. Do not install it in Carbon PC yet.

With no --decoder, the command performs structural checks only. In this case the report field pcm_equivalent is null, not true. Exit code 0 means the requested checks passed (which might be structural-only), 1 means decoded PCM mismatch, and 2 means invalid input or execution failure.

## Synthetic validation without copyrighted files

Run:

    python audio/tools/undercover_mt10_private_bridge_v28.py --self-test --decoder /path/to/vgmstream-cli

This creates one independently generated compressed MicroTalk **silence** frame and one independently generated **nonzero RELP excitation pulse** frame. The real decoder checks each after V28 builds a new PC-style header from the PS2-style source. The original compressed blocks and resulting decoded PCM are identical across the compared versions.

**Verified GitHub Actions run:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41210582210

**Automated tests:** 102/102 Python synthetic regressions passed, plus the separate real official vgmstream self-test for both synthetic MicroTalk variants.

Source and tests:
- [V28 converter](../tools/undercover_mt10_private_bridge_v28.py)
- [20 new V28 tests](../tests/test_undercover_mt10_private_bridge_v28.py)
- [V25 structure validation](../tools/schl_wrapper_audit_v25.py)
- [V22 PCM comparison](../tools/ea_mt10_pcm_equivalence_v22.py)

## Remaining limitations

- The PC-shaped header is experimental; Carbon PC playback is unverified.
- The original 22,050 Hz compressed samples are preserved, not resampled/re-encoded to 24,000 Hz.
- Mono original PS2 MT10 files only; stereo and nonstandard extra header patches are intentionally rejected.
- No genuine Undercover speech was decoded in the GitHub test runner, which has no game archives.
- Police IDX/BIG bank integration, CSI/EVT mapping and actual in-game pursuit radio remain unverified.
- Keep original recordings, reconstructed ASF, decoded WAVs and generated audio fingerprints private, never in public GitHub.

**Next milestone:** run V28 with an authentic private Undercover PS2 mono voice and compare decoded PCM hashes before attempting any in-game tests.