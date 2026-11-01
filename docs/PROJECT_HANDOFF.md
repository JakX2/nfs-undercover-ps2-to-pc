# Project handoff: Undercover PS2/Wii to Carbon PC

**Status as of 2026-11-01: offline reverse engineering, NOT a playable port.**
This document is for anyone interested in picking up the work. It is an
evidence and navigation guide, not a claim that any conversion works in-game.

## North star: one reproducible vertical slice

**First useful playable milestone:** render one correctly identified
Undercover scenery object inside the actual Carbon PC engine, in a verified
world sector, using an authorized original Carbon installation. Collision,
navigation and driving through a larger district are subsequent milestones.
A complete Tri-City Bay port is not presently estimable.

Before attempting any installer, native serializer or hook, we need original
PC-world evidence and an independently verified loader ABI. The repository
contains no safe-to-install world modification.

## Verified versus tentative

| Topic | Current evidence | What is *not* proven |
| --- | --- | --- |
| Original Wii example | A single previously authenticated 8,488-byte RedBuilding scenery ROOT; SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`. Candidate 31 aligned 96-byte instance rows, eight 48-byte spatial nodes, 24 candidate 128-byte preculler blocks and 31 auxiliary 32-byte rows. | Independent second Wii scene, actual `0x34107` visibility semantics, geographic equivalence to a PC section |
| Wii geometry -> PC-style model library | Offline RedBuilding 1B/1C/1Z conversion: 731 vertices, 464 triangles, approximately 31 KB output, with synthetic or source-derived offline checks in the relevant work. | Registered Carbon object, verified shader appearance, normal fidelity, texture pack installation, in-game render |
| Wii `0x34107` candidate | 3,072 bytes can equal both `(31+1)*96` and `8*384` for the single original root. | Which size formula, if either, represents actual preculler semantics |
| Carbon PC world serialization | Candidate source-only parsers, framing/overlap checks and separately authored experimental master-table hypotheses. | Original authenticated Carbon PC `0x34105`/`0x34107` disk layout or original `0x34110` row schema |
| Public Carbon resource loader | Pinned 2017 XNFSModFiles source provides historical Carbon resource-loading virtual addresses; separate V63 static PE32 mapping tests use synthetic executables. | Those hook bytes in *our* original executable version, calling conventions, safe hooks or scenery registration |
| Audio, physics and police AI | Independent source-only research tracks in draft PRs. | Full Undercover audio/gameplay playback or runtime behavior integrated in Carbon |

**Test labels matter:** “30/30 passed” or “56/56 passed” typically means
synthetic Python tests in a particular branch, not a game-runtime test.
Optional original-fixture tests can be skipped on public CI. Tests from
different branches should not simply be added together as proof of a port.

No independently authenticated second Wii scenery ROOT or original Carbon PC
world/master pair is currently recorded in the published research baseline.
No first in-game Undercover building, collision or drivable map is verified.

## Where the code lives

`main` presently contains a short project README and audio introduction,
**not** a consolidated copy of the scenery research. Most work resides in
separate **draft pull requests** that were intentionally not merged.

**Start here:**

- [#1 V41–V46 scenery geometry source baseline](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/1).
- [#6 V51 Wii source-aligned scene reader](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/6).
- [#14 V56 source-gated candidate graph](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/14).
- [#16 V58 full-stream candidate discovery](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/16), [#18 V59 same-file manifest verification](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/18), [#20 V60 instance-cohort comparison](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/20).
- [#22 V61 format-neutral Carbon chunk inventory](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/22), [#24 V62 ambiguous/overlapping candidate checks](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/24), [#26 V63 historical Carbon loader address preflight](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/26).
- Independent Carbon-index hypothesis track: [#21](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/21), [#23](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/23), [#25](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/25), [#27](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/27).
- Independent [audio PR #4](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/4) and [AI/physics PR #2](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/2).

### How the draft branches relate

There are **two parallel V60/V61/V62 lines**, not a single linear release
sequence. Numbers are historical research labels, not released software versions.

```text
#1 -> #3 -> #6 -> #7 -> #8
                        |-> #9  -> #11 -> #13 (full-stream source-snapshot line)
                        |-> #10 -> #12 -> #14
                                            |-> #15 -> #16 -> #18 -> #20 -> #22 -> #24 -> #26
                                            |-> #17 -> #19 -> #21 -> #23 -> #25 -> #27

#2 = separate AI/physics draft from main
#4 = separate audio draft from main
```

Do not cherry-pick a later PR assuming it is independent of its base.
Check the PR's **base branch** before running tests or proposing a merge.
The branches can contain overlapping approaches, different parsers and
speculative assumptions. A source review and a minimal consolidation are
needed before declaring an established baseline on `main`.

## High-impact next contributions

1. **Make the research accessible without original games:** Consolidate a
   small, reviewed, source-only testable branch. Start with
   [help-wanted issue #29](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/29).
2. **Verify real Carbon world and index data:** Analyze locally owned,
   independently authenticated Carbon PC original source archives and
   loader behavior; share *only* sanitized derived findings and synthetic
   tests. Start with [help-wanted issue #28](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/28).
3. **Then aim at one safe in-game demonstration:** After runtime ABI,
   original streaming ownership and material dependencies are established,
   test a *known-good* Carbon resource in a separate test installation,
   followed by a single Undercover object. Document actual observed
   behavior rather than treating a successful load call as a rendered scene.

Physics and audio development can continue in their independent branches,
but neither makes the world-port blocker disappear.

## Collaboration / distribution

Do **not** commit or attach original EA executable files, BUN/ELF/TPK
archives, extracted copyrighted scene chunks, textures, converted meshes or
private filename/path manifests. Keep original game files local. Use synthetic
fixtures in public tests. Derived hashes and offsets are useful integrity
metadata but do **not** authenticate file provenance by themselves.
Please inspect reports for sensitive strings before publishing.

[CONTRIBUTING.md](../CONTRIBUTING.md) explains how to run the source-only
work and describe evidence honestly. There is no guaranteed completion date
and no verified playable build. A newcomer can still improve the project's
future by making even one narrow result reproducible.
