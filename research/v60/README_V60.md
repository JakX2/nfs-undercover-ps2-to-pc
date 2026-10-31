# V60: Cross-stream candidate-scene cohorts and falsification shortlist

**Read-only metadata research. No game assets, extracted bytes, or native world patch.**

## Research problem

V58 detects candidate scenery ROOTs inside game archives and reports their whole
ROOT SHA-256. However, a changed `0x34107` mask, header or auxiliary record
can change that ROOT hash without changing any of its `0x34103` scenery
instances. Two distinct ROOT hashes are therefore **not necessarily two
independent scene instance datasets**.

The only previously authenticated original Wii RedBuilding ROOT in the project
has 31 candidate instance rows, eight candidate 48-byte spatial tree nodes and
24 candidate 128-byte preculler blocks. Its 3,072-byte `0x34107` fits both
`(31+1)*96` and `8*384`. The arithmetic cannot identify the actual
preculler semantics. We should prioritize new authenticated scenes that do not
accidentally satisfy both candidate equations.

## Implementation

1. V58 now emits four SHA-256 **payload hashes only** for candidate
   `0x34101` scenery-header, `0x34103` instance, and optional
   `0x34105` spatial-tree and `0x34107` preculler chunks. No extracted
   original chunk bytes, coordinates, filenames or local paths are published.
2. V60 ingests 1–128 **metadata-only** V58 JSON reports. It checks schema,
   archive/root fingerprints, source hints, ranges, output counts and
   contradiction between repeated exact ROOT fingerprints.
3. It groups exact duplicate ROOTs and candidate Wii scenes sharing an identical
   instance payload. A different preculler or auxiliary byte does not by
   itself count as another candidate scene instance payload.
4. It evaluates two **numeric hypotheses only** on distinct Wii ROOTs that
   pass the existing V57 graph checker:

   - `preculler_bytes == (candidate_instances + 1) * 96`
   - `preculler_bytes == candidate_tree_nodes * 384`

   Candidates satisfying exactly one of these are listed first for **source
   authentication and independent replication**. This does not resolve the
   hypotheses without trustworthy original-game provenance.
5. Reports preserve `independent_original_Wii_scenes_authenticated=false`
   and `Carbon_PC_preculler_serialization_proven=false`, regardless of the
   number of files or hashes.

## Local usage

First, independently obtain **original game archives you are authorized to
inspect** and measure their whole-file SHA-256 digests. Run the V58 scanner
using `--expected-archive-sha256`, once per distinct archive, to generate
local metadata-only reports. Then compare:

```sh
python research/v60/v60_candidate_cohorts.py \
  --inventory /private/reports/wii_master_01.json \
  --inventory /private/reports/wii_master_02.json \
  --report /private/reports/v60_candidate_shortlist.json
```

V60 requires each V58 source archive to have had a trusted expected-file
digest supplied. If you only have exploratory unguarded V58 metadata, add
`--allow-unguarded`; the resulting report explicitly records the number of
unguarded inputs and **still authenticates no original game source**.

V58 reports generated before this PR lack the component payload fingerprints
and must be regenerated using the updated V58 scanner. Rehashing a game
archive during this scan does not itself establish source authenticity.
Avoid modifying game archives while scanning.

## Testing

```sh
python -m unittest discover -s research/v60 -p 'test_v60.py' -v
python -m unittest discover -s research/v58 -p 'test_v58.py' -v
```

25 new synthetic V60 cases include modified-preculler same-instance
detection, all four candidate arithmetic outcomes, duplicate ROOTs,
contradictory metadata, strict hash guards, output truncation, CLI
non-overwrite behavior, and unchanged synthetic archive files. No original
Undercover or Carbon copyrighted inputs are committed to public CI.

## Next actual evidence gate

Inspect a *real*, second independently authenticated Undercover Wii scenery
ROOT and an authenticated Carbon PC scenery scene. The shortlists only tell
us what data is most informative to check. Real preculler semantics, Carbon PC
binary serialization, loader registration, relocation, materials, collision,
navigation, and in-game behavior remain unverified. No installable artifact.
