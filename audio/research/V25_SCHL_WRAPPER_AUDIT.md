# V25: Strict SCHl post-header identity + optional real PCM comparison

**Status:** V25 is committed to the audio research branch. The newly extended **58-test synthetic** suite and official decoder-on-generated-PCM job passed on GitHub Actions. **No real Undercover EA-MT10 file has been decoded or PCM-compared in this environment.**

## Why this test matters

V20 rebuilt the SCHl header of a user-extracted Undercover PS2 voice to resemble an observed Carbon PC header, leaving the compressed block sequence in place. V21 applied the same header operation while rebuilding isolated IDX/BIG containers.

V25 gives that preservation claim a strict, independent binary check on *two individual already-extracted SCHl files*. This lets us reject a corrupted or accidentally modified stream before interpreting a passing decoder run.

The independently read [vgmstream EA SCHl parser](https://github.com/vgmstream/vgmstream/blob/master/src/meta/ea_schl.c) identifies SCHl, SCCl, SCDl and SCEl chunk types. Its [blocked layout handler](https://github.com/vgmstream/vgmstream/blob/master/src/layout/blocked_ea_schl.c) reads each little-endian SCDl block's sample count at relative byte offset +8.

**Additional source-based insight:** vgmstream enables EA's newer PCM-block codec behavior for header version 3 and for version 2 on PC. That suggests the v3 PS2 / v2 PC version pairing need not automatically imply a different MicroTalk block interpretation *inside vgmstream*. This is a hypothesis about that decoder's implementation, **not** evidence of Carbon PC's runtime behavior or decoded PCM equivalence.

## Independent structural checks

[V25 source tool](../tools/schl_wrapper_audit_v25.py) opens exactly two user-supplied, little-endian individual SCHl recordings, subject to a 64 MiB size cap. It:

1. Parses the outer SCHl, optional SCLl, one SCCl, SCDl blocks, and SCEl terminator with strict sizes and boundaries.
2. Verifies one SCCl block count equals the number of SCDl blocks for the intended NFS speech format.
3. Verifies SCDl sample counts are positive, calculates the sum, and hashes all SCDl blocks.
4. Independently hashes the bytes **after** the variable SCHl header. These bytes must remain identical even if the two SCHl header lengths differ.
5. Allows up to 255 bytes of zero-valued alignment padding after SCEl, which is excluded from the audio comparison; rejects nonzero trailer bytes.
6. Reports per-file sizes, SHA-256 hashes, header lengths, preserved segment hashes and boolean checks in JSON.

Only structural identity is claimed by default. The program intentionally has no writer for game assets, audio banks or compressed audio. It will refuse to overwrite an existing JSON report.

### Test a pair of private local recordings

Start with two corresponding *individual SCHl streams* from the user's local V19–V21 export workflow, not the full IDX/BIG containers. Both files must start with the bytes SCHl.

~~~powershell
python audio/tools/schl_wrapper_audit_v25.py --original "D:\NFS_Audio_LAB\uc_original.asf" --experimental "D:\NFS_Audio_LAB\uc_pc_style.asf" --report "D:\NFS_Audio_LAB\v25_structure.json"
~~~

This default test does **not** decode and does not write audio. It produces only a JSON audit report.

To run both the structural check **and** real PCM decoding using the official installed decoder:

~~~powershell
python audio/tools/schl_wrapper_audit_v25.py --original "D:\NFS_Audio_LAB\uc_original.asf" --experimental "D:\NFS_Audio_LAB\uc_pc_style.asf" --decoder "D:\Tools\vgmstream\vgmstream-cli.exe" --report "D:\NFS_Audio_LAB\v25_pcm.json"
~~~

When --decoder is supplied, V25 uses the V22 decoder harness to decode both streams to **temporary WAVs**, compare PCM16 sample bytes, rate, channels and frame counts, and then delete the temporary WAVs. It keeps a decoder executable hash and the comparison result in the JSON report.

**Exit codes:** 0 for the requested checks passing; 1 if a well-formed pair differs structurally or in decoded PCM; 2 for invalid files, a missing decoder, unsafe report destination, or other execution errors.

Note: If the original and experimental compressed audio truly are the same, but the PC-style header alters the way vgmstream decodes it, the PCM equality check will fail as intended. PCM identity must be independently demonstrated on real source clips.

## Test evidence and limitations

Source and tests:
- [V25 auditor](../tools/schl_wrapper_audit_v25.py)
- [V25 generated-fixture tests](../tests/test_schl_wrapper_audit_v25.py)
- [V22 independent PCM comparator](../tools/ea_mt10_pcm_equivalence_v22.py)

**Verified CI:** 58/58 synthetic tests, plus the official vgmstream CLI integration test using original generated PCM16LE. https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41208600250

The synthetic V25 tests intentionally exercise malformed chunk boundaries, wrong counts, altered audio bytes, altered sample counts, different header lengths, safe report paths, and mocked PCM equality/mismatch. Those tests do not use original game recordings or call the MicroTalk decoder. The separate official CLI job verifies only TXTH-described generated PCM.

## Unresolved

- Actual MicroTalk EA-MT10 input accepted and decoded from Undercover PS2.
- PCM identity for the V20/V21 experimental PC-shaped SCHl version.
- Carbon PC's own player handling of a 22,050 Hz stream and its MT10 block metadata.
- Correct police CSI/EVT routing and installation of a complete Carbon-compatible bank.
- Hearing the original police dialogue in-game.

Keep any source recordings, WAVs, and reconstructed banks privately. Only commit code, synthetic tests and non-sensitive metadata to GitHub.
