# Carbon PC native post-scene: blind third-section discovery (V4)

**Date:** 2026-11-04  
**Project:** NFS Undercover PS2/Wii → Carbon PC world bridge  
**Scope:** source-only, owner-local, **read-only** research. No game archive contents, original binary records, texture/mesh data, or per-model identities are included. Original Carbon PC files were **not** accessed in this V4 development run. No retail Carbon build was run or modified.

## Result of this milestone

V3's strict field-hypothesis screen requires three independently authenticated Carbon PC sections with the same exact native layout. Prior original-source work authenticated two sections, **141** (six native `0x372xx` groups) and **142** (one native group). **V4 does not assert that a third eligible section exists.** It automates the selection so the next original-source run can answer the question without manually choosing a promising-looking section after inspecting field matches.

The new `carbon_pc_postscene_control_discovery.py`:

1. Parses the complete original Carbon PC `L5RB.BUN` 92-byte `0x34110` section index using the existing bounded `stream_rows` validation. It checks regular files, source lengths and baseline presence.
2. Visits **every** indexed section in ascending numeric ID order, reading only that section's bounded `STREAML5RB.BUN` range. Zero-length / oversized sections and nonmatching PC texture-root prefixes are classified separately.
3. Applies the **existing strict** `_private_section_record` validator to every texture-prefixed candidate, requiring the known Carbon PC texture→geometry→scenery→`0x372xx` envelope, a complete native PC indexed eSolid root and valid scenery model-hash slots. Unsupported layouts are counted as unsupported, **not as proof that the section contains no such resources**.
4. Retains only disjoint, aligned, independently authenticated sections. If two different sections have byte-identical native post-scene headers and opaque group payloads, only one can vote in the cross-section analysis. The baseline IDs win deterministic tie-breaking. All exact-match tests use the same verified section-local scene/solid hash sets as V1–V3.
5. Runs the existing V2 leave-one-section-out comparison, V3 byte-lane/endian negative controls and V3 strict all-informative-words triage over **every accepted nonduplicate suffix**, rather than cherry-picked IDs. A strict-screen result may be evaluated only with ≥3 independent unique-suffix controls.
6. Emits only **aggregate counts, accepted section IDs, word-slot indices and booleans**, never original asset bytes, per-model hashes, absolute stream offsets or geometry exports.

### Passing synthetic-only controls

**119/119 tests passed** when running the V1–V4 suite in a clean local Python session. V4 adds **21 tests**, including automatic third-control selection, insufficient-controls output, malformed candidate rejection, missing/invalid known baselines, identical suffix deduplication, deterministic baseline preference, bounded census refusal, no input modification, source-path alias/symlink rejection, and unexpected parser errors propagating instead of being hidden. Tests use **fabricated data and mock authenticated records**, *not* game-original resources. V4 cannot claim real-source verification until run by the owner with extracted original files.

## Running the original-source audit privately

Put this kit's Python files next to the existing `research/world_bridge` modules from draft PR #33. Those include `carbon_pc_native_postscene_layout_gate.py` and `geometry_hash_control.py`, which V4 imports only when inspecting the original Carbon sources.

```powershell
# Entire synthetic regression suite, no game installation required:
python -m unittest -q test_carbon_pc_postscene_dependency_probe.py test_carbon_pc_postscene_cross_section_gate.py test_carbon_pc_postscene_lane_controls.py test_carbon_pc_postscene_control_discovery.py

# Source-original READ-ONLY blind scan. Use your privately extracted files:
python carbon_pc_postscene_control_discovery.py `
  --carbon-bun 'C:\PrivateBackup\L5RB.BUN' `
  --carbon-stream 'C:\PrivateBackup\STREAML5RB.BUN'
```

The default baseline check requires **sections 141 and 142**, previously validated on authentic Carbon PC source. The output field `independent_three_section_gate` is `EVALUABLE` only when ≥3 authenticated sections with distinct exact post-scene payloads have survived the scan. Otherwise it is `INSUFFICIENT_CONTROLS`. `first_additional_control_beyond_baselines` identifies the lowest-numbered additional accepted section, if any.

The `strictly_authenticated_section_ids` array lists original *section numbers* to make this experiment reproducible; it does **not** include model IDs, texture IDs, asset names or hash inventories. No `--write`, game-path override, binary writer or patch operation exists.

## Important limitations

- V4's envelope parser is intentionally based on the **previously verified 141/142 structure**. A Carbon PC section using a different but valid native layout may be rejected. Rejection is *not* an absence claim. If no third section passes, the next appropriate task is a separate looser framing **census**, not weakening the hash-reference criteria.
- The prefix check is a cheap prefilter; native authentication takes place only after the full geometry-index, scenery and post-scene validators pass.
- Distinct file offsets are a necessary condition for independent sources, not a guarantee of independent content. Byte-identical suffixes are collapsed before the V3 vote; shared model hashes are marked ambiguous by V2.
- Passing the strict screen would remain an **ID-correlation hypothesis**, not proof that a field is a model registration pointer, table offset, relocation target or runtime loader ABI. A negative strict screen also cannot exclude optional or mixed-purpose fields.
- Actual Undercover→Carbon world loading remains blocked by object identity, material/texture identity coverage, native registration semantics, geometry validity in the retail loader, collision, roads and streaming. The prior byte-budget result is **capacity only**.

**Next source-backed question:** Does the owner's original Carbon PC RB stream contain at least one additional strict-profile section beyond 141/142? Only a private original-file run can answer that. Do not commit original assets, game binaries, extracted chunks or resource inventories to GitHub. PR #33 should remain a draft; `main` should remain unchanged.
