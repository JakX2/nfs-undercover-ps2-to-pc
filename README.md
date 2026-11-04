# NFS Undercover PS2/Wii → Carbon PC

Research repository for a **native-format Undercover PS2/Wii → Carbon PC porting investigation**. This is **not a playable PC port**.

## Public original-source milestone: V5 (2026-11-04)

A read-only examination of the owner's original Carbon PC RB world stream found **seven sections with complete native `0x372xx` post-scene framing**, and **six sections** that also pass strict scenery/PC indexed-solid integrity checks.

Across **14 post-scene control groups** in those six sections, two `0x37250` payload fields, **u32 word 17 (`+0x44`) and word 19 (`+0x4C`)**, are identical and both resolve to the same section-local scenery and geometry model hash. These are **candidate identity fields**, not confirmed pointers or engine-registration instructions.

Read the [original-source V5 findings](research/CARBON_PC_POSTSCENE_ORIGINAL_RB_V5.md) for provenance, exact scope, counterexamples, and limitations.

## Research code and next milestones

[Draft research PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33) contains the existing source-only world bridge, asset-format tools and synthetic regression tests. The draft remains experimental and should not be mistaken for a working PC world installation.

Immediate research targets: independently verify the candidate model-hash fields outside the current Carbon RB controls, understand the alternate geometry profile in section 299, and determine native resource reference/relocation semantics before designing any reversible runtime test.

Earlier work includes V41 native scenery model conversion and V43–V46 scenery spatial/opaque-chunk analysis. Those were offline results, not in-game validation.

## Safety and distribution

Original game files, extracted binary records, textures, models, patched archives and executables **are not distributed here**. Source scripts read game files supplied privately by the owner. Do not install experimental output into a live game.

**No playable Undercover PC port, completed streaming integration, collision, police AI, or in-game scene rendering is claimed.**
