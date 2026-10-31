# V58: source-guarded archive to scene evidence bridge

**Research-only. Read-only. No original copyrighted game files in GitHub.**

## Motivation

V55 and V57 can analyze individually extracted scenery ROOTs and test the
speculative Wii 96-byte instance / 48-byte spatial-node / 128-byte preculler /
32-byte auxiliary candidate structure. This is useful but cannot on its own
find a second original scenery scene inside the user's full game archive.

V58 bridges these steps by scanning a user-supplied archive for bounded
ROOTs, applying Wii-candidate graph validation, and recording candidate
offsets and SHA-256 fingerprints.

## Command

Run locally using Python 3.10+ with your own original game archive.
The Windows path is illustrative, not a confirmed filename:

```powershell
py -3 research/v58/v58_stream_scene_bridge.py `
  --archive "D:\OriginalGames\UndercoverWii\TRACKS\TRACKS_MASTER.BUN" `
  --source-hint wii `
  --endian little `
  --report "D:\PrivateResearch\v58_summary.json" `
  --private-manifest "D:\PrivateResearch\v58_local_manifest.json"
```

Add `--expected-archive-sha256` with a separately established archive
digest if available. A file hash verifies bytes, not game provenance.

The metadata-only report contains offsets, source/ROOT hashes, child tags,
candidate counts and validation statuses, but **no binary data or source
path**. The optional private manifest contains local absolute archive paths
and expected hashes so existing V55/V57 read-verified-root tooling can
reinspect each candidate. **Do not publish private manifests unreviewed.**

## Source and format limitations

- The root signature is `0x80034100`, with user-selected byte order.
- Source-observed direct children `0x34101` and `0x34103` must exist.
  Other original scenery layouts may be missed.
- `--source-hint wii` applies the candidate Wii spatial graph checker.
  `carbon_pc` and `unknown` *skip* Wii checks. Carbon PC on-disk
  `0x34105/0x34107` ABI remains independently unverified.
- Identical ROOT SHA-256 hashes are duplicates, not independent scenes.
  Different hashes alone are **not** independent provenance authentication.
- The scanner hashes the same read-only archive mapping twice, checks
  filesystem metadata and path identity, but does not make an atomic
  filesystem snapshot. Do not modify input archives during scanning.
- Matching a candidate layout is not proof of preculler semantics.
- Signature/root count limits and exclusive new-file creation protect
  against uncontrolled scanning and overwriting inputs.
- No textures, models, proprietary chunks, game patches or executable
  bytes are distributed. `safe_to_install` remains false.

## Synthetic test suite

```sh
python -m unittest discover -s research/v58 -p 'test_v58.py' -v
```

24 asset-free tests cover candidate offset discovery, duplicated/distinct
hashes, invalid geometry references, byte-order selection, malformed framing,
digest guards, limit refusal, root-reader manifest interoperability,
CLI output isolation and input immutability. Private original-Wii fixture
tests remain conditional in the V56 suite, not shipped in public CI.

## Next scientific step

Use the tool locally against an independently sourced Wii game archive and
identify a second original scene with a recorded source location.
Then compare independently sourced Carbon PC world roots under separately
established schema hypotheses. Before that, no result proves Carbon's loader
can render, stream, collide with or navigate through these objects.
