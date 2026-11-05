# NFS Undercover PS2/Wii → Carbon PC

Research repository for an **offline native-format porting investigation**. This is **not yet a playable PC port**.

## Original-source world-stream findings

**V6, 2026-11-05:** Carbon PC RB section 299 uses two serialized eSolid header values: 73 solids with `0x00000016`, and four with `0x00400016`. The version-aware offline reader verifies all 77 indexed identities and six post-scene group matches. Across seven RB sections, **20/20** `0x37250` record groups have identical model-hash candidate fields at `+0x44` and `+0x4C`, backed by local scenery and solid indexes. This is *not* evidence of pointer semantics or runtime registration.

An independent, bounded scan of 961 Carbon PC RA sections found **no match for the exact RB-specific post-scene sequence**; RA's format must be investigated separately. This is a format-profile negative, not evidence that RA lacks scenery or models.

Read [V6 findings and limitations](research/CARBON_PC_POSTSCENE_V6_VARIANT_AND_RA.md) and the earlier [V5 original-source controls](research/CARBON_PC_POSTSCENE_ORIGINAL_RB_V5.md).

## Prototype experiment: November 7, 2026

A source-only [V8 Windows prototype readiness runbook](research/CARBON_PC_FIRST_RUNTIME_PROTO_V8_RUNBOOK.md) documents a 55-test V7/V8 handoff for a reversible Undercover PS2 texture-in-Carbon PC test. V8 verifies both installed RB files plus required Python dependencies before staging; any installation and restoration require explicit owner-controlled actions.

**No game-side rendering or playable Undercover PC prototype has been verified.** A real Windows launch and before/staged/restored visual evidence are still needed.

## Undercover scenery material coverage: V9 (2026-11-05)

A read-only owner-original audit reproduced **268 PS2 eSolid occurrences and 76,348 triangles** across eight geometry packs. **46/48** texture identities actually used by Undercover RB scenery have indexed images in the source RB packs. A stricter external-bank scan found **none of the two remaining identities in fully validated PS2 texture indexes** within Undercover `GLOBAL`, `FRONTEND`, `CARS`, or `Unknown`. The car bank uses unsupported image layouts in this specific parser, so this is **not a global absence claim**. Prefer the six fully image-backed source geometry packs when preparing a constrained offline native-asset test; no in-game world import has been proven.

See [V9 source-bank audit](research/UNDERCOVER_PS2_EXTERNAL_MATERIAL_IMAGE_V9.md). The standalone Python V9 scanner and 35 synthetic tests are delivered in the separate source-only research kit.

## Research code and work in progress

[Draft source-only research PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33) hosts the broader experimental world-bridge code and tests. The separate V6 version-aware parser is included in the downloadable V6 research kit, not yet committed to that PR. The public V6 report is aggregate-only.

Next: classify the four alternative section-299 solids, decode RA's distinct section layouts, and establish actual Carbon loader behavior before building any private, reversible installation experiment.

Earlier work includes V41 native scenery conversion and V43–V46 scenery spatial/opaque-chunk analysis. All are offline format-research milestones.

## Distribution and runtime boundaries

No original game files, extracted asset payloads, models, textures, executable patches or modified retail archives are distributed here. All game-source analysis uses privately supplied originals.

**No Undercover gameplay, native in-game rendering, world streaming, collision or driveable PC build has been verified.**
