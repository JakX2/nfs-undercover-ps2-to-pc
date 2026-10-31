# V31: Offline BIG scanner and mandatory real-PCM verification of one selected mono MT10 stream

**Status: synthetic GitHub Actions tests pass; genuine Undercover source audio has NOT yet been opened or decoded in this environment.**

V31 adds a local-only extraction bridge between an extracted Undercover PS2 BIG archive and the independently tested V28 EA-MT10 PS2-to-PC-style header rewrapper. It is designed to get our real-voice experiment unstuck without storing copyrighted game recordings in the repository.

## The new tool

Source: [undercover_big_voice_scan_v31.py](../tools/undercover_big_voice_scan_v31.py).

The scanner reads a local .BIG file in small chunks without loading the entire archive. It looks for literal SCHl chunk signatures and validates each possible recording by reading EA chunk boundaries, SCCl declared count, SCDl block sample counts, SCEl terminator, and the original PS2 EA variable header. It *only* lists the source format currently supported by V28: **PS2 platform 5, header version 3, mono, EA-MT10 codec2=4**. The archive remains read-only.

Crucial constraints:
- This is a validated **raw-SCHl signature scanner**, not a general IDX/BIG directory/index parser. It works only when recordings are stored contiguously and unobfuscated inside the BIG. It does not infer audio group identity or police event IDs.
- Scanner offsets point to compatible mono MT10 audio streams, **not necessarily police dialogue**. CSI/EVT/IDX event mapping is required to prove which dispatch line an offset belongs to.
- It does **not** read split .z01/.z02/.zip archive sets directly. Unpack the parts privately first so you have the underlying .BIG file.
- The scanning default limit is 250 candidates. It can search for up to 20,000 using --max-results. If it returns no candidates, that does not prove the archive lacks police speech; format assumptions or bank structure may differ.

## How to run locally on original game files

Put all parts of ExtractedSOUNDucps2.z01, .z02 and .zip in the same folder and use an archive manager that supports split ZIP archives (such as 7-Zip) to extract the archive privately. Do not publish extracted assets.

From the GitHub repository root, adjust the paths in the following Windows PowerShell command:

    python audio/tools/undercover_big_voice_scan_v31.py scan --big "D:\NFS_UC_PS2\SOUND\POLICE.BIG" --max-results 250 --report "D:\NFS_AUDIO_LAB\v31_candidates.json"

Here POLICE.BIG is a placeholder path, **not a claim about the actual extracted filename**. Use the real .BIG file path found in your extracted archive. The scan generates JSON listing only offsets, lengths, sample rate, block count, and sample totals. No audio is extracted.

Choose one printed candidate offset. Then run with the official vgmstream-cli binary installed locally:

    python audio/tools/undercover_big_voice_scan_v31.py verify --big "D:\NFS_UC_PS2\SOUND\YOUR_FILE.BIG" --offset 0x123456 --decoder "D:\Tools\vgmstream\vgmstream-cli.exe" --out-dir "D:\NFS_AUDIO_LAB\v31_private_result"

Replace 0x123456 with an **actual offset reported by scan**. The output folder must not already exist.

Verify mode:
1. Validates the original stream offset and boundaries.
2. Copies only one original SCHl stream to a temporary private folder.
3. Calls V28 to reconstruct an experimental PC platform0/version2 header, while preserving original compressed bytes after SCHl.
4. Calls the actual independent upstream vgmstream-cli twice and checks strict decoded-PCM16 equality, rate, channels, samples and hashes.
5. Deletes temporary source and WAV/ASF media, retaining **only report.json** in the new private output folder.
6. **Requires --decoder.** A header-only pass never counts as a successful verify. A failed decode/mismatch results in a nonzero exit.

Use --keep-pc-shape only if you explicitly want to retain the experimental ASF file **locally** for further offline testing. Do not install it in the live game yet.

Even if verification passes, the report field actual_undercover_provenance_confirmed is false until we link the file to an identified original bank/recording and confirm that it is a police voice. And carbon_pc_runtime_tested remains false.

## Reproducible synthetic GitHub Actions evidence

Run this self-test with the official CLI, *without any game assets*:

    python audio/tools/undercover_big_voice_scan_v31.py self-test --decoder /path/to/vgmstream-cli

The test generates a mock BIG containing junk, a false SCHl signature and two valid synthetic compressed mono MicroTalk streams: a three-frame single-SCDl stream from V30, and the same three-frame sequence across three separate SCDl chunks from V29.

Using a small scan-block size of 13 bytes, the V31 code finds the original generated candidate offsets 107 and 330 and rejects the false signature. It extracts both streams privately, invokes V28 and the *actual official MicroTalk decoder* for both, and verifies that their decoded PCM hashes are exactly the same.

Recorded decoded PCM SHA-256:

    4881991e5814b8e901efa85c44d4ab0c6c7b610b5ea8413b90c7c972b9ade1d6

**Verified CI:** https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/41212591848

**Automated suite:** **162/162 synthetic regressions passed**, including the new scanner/selection/decoder-failure tests. A separate GitHub Actions job downloaded and ran the official vgmstream CLI on all earlier cases plus V31's complete mock-BIG extraction/PCM comparison.

## Limitations / next step

The user's original source archive parts are listed in the Project conversation but the local file execution tools have not been available, so there is still **no real Undercover voice decoded in this turn**. We cannot claim any original police dialogue works yet. A `.BIG` signature alone also does not establish police event identity.

The next real experiment is to point V31 at an extracted original PS2 BIG, choose a verified candidate and run the strict private PCM gate. Then use IDX/CSI/EVT to associate the offset with a police event before any Carbon PC runtime test. Stereo, encrypted/obfuscated or independently framed streams require additional parsing support.

No original game media, compressed source samples, or reconstructed asset files are distributed. This tool never edits a game installation.