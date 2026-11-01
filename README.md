# NFS Undercover PS2/Wii → Carbon PC

> **Research project, not a playable PC port.** No original EA game files or
> installable patches are distributed. There is no verified in-game
> Undercover scenery render, working collision, or complete map conversion.

This project investigates bringing scenery, streaming, gameplay and audio from
the PS2/Wii versions of **Need for Speed Undercover** into the **Need for
Speed Carbon PC** engine. The end goal is a small, accurately placed,
observable Undercover world sector before anyone attempts a larger map.

### Want to pick up the project?

**[Read the project handoff](docs/PROJECT_HANDOFF.md)** for an evidence-based
status report, the major technical blockers and a map of the draft branches.

**[Start contributing](CONTRIBUTING.md)** for an asset-free first task, Python
test commands, source-provenance standards and safety guidance.

Current public help-wanted tasks:

- [Make the source-only research reproducible for new contributors (issue #29)](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/29). No game copy required.
- [Verify original Carbon PC world-scene/master-index data (issue #28)](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/28). Needs locally owned original game inputs and serious binary-format work.

### What's actually working?

- Offline Wii RedBuilding geometry extraction and PC-style mesh conversion
  have been investigated with source-derived checks.
- A single exact original Wii RedBuilding scenery ROOT has been pinned and
  analyzed; the interpretation of its spatial/preculling data is still
  partly hypothetical.
- Asset-free test suites cover synthetic frame parsing, scene graph checks,
  archive source integrity, candidate index hypotheses, and an early static
  PE32 Carbon resource-loader preflight.

**Crucial missing proof:** an independently authenticated original Carbon PC
scenery stream/master-index pair, the Carbon engine's actual serialized
scene/index ABI, and a safely demonstrated in-game building. Tests passing
on synthetic input do not establish any of those.

### Finding the code

`main` intentionally does **not yet contain** the reviewed scenery research
stack. The work currently lives across draft PRs, some **parallel** and
sharing version labels. A few starting points are
[geometry baseline #1](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/1),
[Wii scene graph #14](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/14),
[Carbon chunk probe #22](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/22),
[chunk overlap checks #24](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/24),
and [Carbon loader preflight #26](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/26).

The [handoff](docs/PROJECT_HANDOFF.md) shows the actual branch relationships.
Don't assume a V-numbered PR can be merged without its parent research PR.

### Important legal and technical boundaries

Do **not** commit or upload copyrighted game executables, original chunk
files, BUN/ELF/TPK archives, textures, models, audio or private paths.
Research should use authorized files locally and share source-only tools,
synthetic tests and carefully sanitized derived evidence.

Do not install experimental scene writers or old binary hooks into your
regular game installation. A source-only model/loader hypothesis is not a
verified, installable Carbon modification.

There is no completion date. **A reproducible first in-game world sector is
the meaningful technical milestone**, and volunteers can help reach it even
without committing to a full port.
