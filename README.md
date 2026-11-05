# NFS Undercover PS2/Wii → Carbon PC

Research repository for an **offline native-format porting investigation**. This is **not yet a playable PC port**.

## Original-source world-stream findings

**V6, 2026-11-05:** Carbon PC RB section 299 uses two serialized eSolid header values: 73 solids with `0x00000016`, and four with `0x00400016`. The version-aware offline reader verifies all 77 indexed identities and six post-scene group matches. Across seven RB sections, **20/20** `0x37250` record groups have identical model-hash candidate fields at `+0x44` and `+0x4C`, backed by local scenery and solid indexes. This is *not* evidence of pointer semantics or runtime registration.

An independent, bounded scan of 961 Carbon PC RA sections found **no match for the exact RB-specific post-scene sequence**; RA's format must be investigated separately. This is a format-profile negative, not evidence that RA lacks scenery or models.

Read [V6 findings and limitations](research/CARBON_PC_POSTSCENE_V6_VARIANT_AND_RA.md) and the earlier [V5 original-source controls](research/CARBON_PC_POSTSCENE_ORIGINAL_RB_V5.md).

## Research code and work in progress

[Draft source-only research PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33) hosts the broader experimental world-bridge code and tests. The separate V6 version-aware parser is included in the downloadable V6 research kit, not yet committed to that PR. The public V6 report is aggregate-only.

Next: classify the four alternative section-299 solids, decode RA's distinct section layouts, and establish actual Carbon loader behavior before building any private, reversible installation experiment.

Earlier work includes V41 native scenery conversion and V43–V46 scenery spatial/opaque-chunk analysis. All are offline format-research milestones.

## Distribution and runtime boundaries

No original game files, extracted asset payloads, models, textures, executable patches or modified retail archives are distributed here. All game-source analysis uses privately supplied originals.

**No Undercover gameplay, native in-game rendering, world streaming, collision or driveable PC build has been verified.**
