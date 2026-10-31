# V62: candidate-chunk overlap and false master-signature triage

**Read-only metadata analysis. No original game bytes, private paths, PC index
schema assumptions, writer, executable patch, or installable mod.**

## Problem

V61 scans a local original Carbon PC archive for tentative scenery ROOT
`0x80034100` and master `0x34110` signatures. A signature alone might
occur *inside another chunk's payload*, and competing payload-length and
total-length header interpretations can both fit a file. It would be unsafe to
identify a master streaming table merely because one apparent `0x34110`
header is bounded.

V62 is a **metadata-only second-stage interval audit** to expose this
ambiguity without deciding what the real engine loader does.

## Changes to V61 output

V61 now records:

- `end_offset_exclusive`: end of each candidate frame under its length
  interpretation;
- `framed_chunk_sha256`: full header-plus-payload hash, distinct from the
  existing payload SHA-256.

These values do not contain original game data. Existing V61 tests remain
unchanged, and the JSON schema name is preserved for compatibility. V62
requires these new fields; older V61 reports must be regenerated.

## V62 analysis

- Validates the V61 archive SHA-256, input schema, candidate bounds,
  framed/payload hashes and nonduplicated interpretations.
- Requires a trusted *expected archive digest* to have been checked by V61,
  by default. `--allow-unguarded` explicitly permits exploratory reports.
  Even guarded reports **do not authenticate the source edition**.
- Uses sorted interval endpoints to flag overlapping candidate variants,
  competing modes at the same offset, and `0x34110` master signatures
  starting inside candidate `0x80034100` ROOT spans.
- Separately records master candidates wholly contained inside a ROOT,
  and ROOT candidate ranges containing possible master signatures.
- Preserves every competing variant. A nested `0x34110` signature is
  suspicious as an independent master, **not automatically invalid**.
- Captures the V61 child-frame status without promoting it to a Carbon
  native schema, loader or relocation proof.
- Reads **only the V61 JSON metadata**, not private original archives.
  No filesystem paths or source-game payload bytes enter the new report.

## Run locally

First run V61 on your own original-game archive with an **independently
measured** SHA-256 fingerprint:

```powershell
py -3 research/v61/v61_carbon_chunk_probe.py `
  --archive "D:\Games\Carbon\TRACKS\STREAML5RA.BUN" `
  --expected-sha256 "YOUR_64_HEX_SHA256" `
  --report "D:\PrivateResearch\v61_carbon_metadata.json"
```

The file path is illustrative, not a claim about your specific installation.
Then run V62 without copying the game archive:

```powershell
py -3 research/v62/v62_framing_conflict_gate.py `
  --v61-report "D:\PrivateResearch\v61_carbon_metadata.json" `
  --report "D:\PrivateResearch\v62_frame_conflicts.json"
```

`--allow-unguarded` is available for V61 metadata generated without an
independent expected file digest. `--top N` limits the number of emitted
candidate records while preserving overall conflict counts.

## Tests

```sh
python -m unittest discover -s research/v62 -p test_v62.py -v
python -m unittest discover -s research/v61 -p test_v61.py -v
```

26 synthetic cases cover nested master signatures, master-before/after ROOT,
same-offset payload/total interpretations, contiguous/unparsed candidate ROOT
children, no overlap at exact byte boundaries, digest/metadata guards,
nested framing controls, nonoverwrite CLI behavior, and metadata-only
execution after the synthetic input binary has been deleted.

## Research boundary

Only one original Wii scenery ROOT has been independently pinned in this
project. There is still **no authenticated original Carbon PC master/stream
pair or V42 donor/candidate pair here**. V62 cannot prove Carbon PC
`0x34110` rows, the native scenery ABI, loader relocation, culling, shader
materials, collision, navigation, or in-game rendering. All compatible
reports retain `safe_to_install=false`.

When original Carbon PC evidence becomes available, use V61/V62 to exclude
obvious conflicting *interpretations*, then confirm genuine master/index
ownership through the loader and independent original sections.
