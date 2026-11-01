# Contributing to the Undercover PS2/Wii to Carbon PC research

Welcome! This is a reverse-engineering and preservation research effort, **not
a playable mod**. Useful contributions include reviews, synthetic test fixtures,
binary format evidence, documentation, and careful first-runtime experiments
*after* prerequisite verification.

Please read [the technical handoff](docs/PROJECT_HANDOFF.md) before starting.
The code is not all on `main`; the handoff maps the two parallel scene
research stacks and their draft PR dependencies.

## Quickest asset-free start

You do **not** need an original game archive to run the synthetic tests.

```sh
git clone https://github.com/JakX2/nfs-undercover-ps2-to-pc.git
cd nfs-undercover-ps2-to-pc

# Carbon archive framing. This code is in a draft branch, not main.
git fetch origin research/v62-framing-overlap-conflict-gate
git switch --detach FETCH_HEAD

python -m unittest discover -s research/v61 -p 'test_v61.py' -v
python -m unittest discover -s research/v62 -p 'test_v62.py' -v
```

For the later historical Carbon loader address audit, switch to
`research/v63-carbon-runtime-hook-preflight` and run:

```sh
git fetch origin research/v63-carbon-runtime-hook-preflight
git switch --detach FETCH_HEAD
python -m unittest discover -s research/v63 -p 'test_v63.py' -v
```

These commands require Python 3.10+ and its standard library. Tests build
synthetic archive/PE inputs. In the source branches, some separately named
original-game fixture tests are conditional on a local environment variable,
and are skipped when the private fixture is unavailable. Do not interpret a
green public CI run as an in-game Carbon test.

To work on a specific feature, use `git switch -c your-topic` after
checking out its intended base branch, or fork and open a PR against that
same base. Avoid stacking onto `main` unless the change is independently
reviewable and its required source code already exists there.

## Good first contribution

Start with [issue #29: make the draft research stack easier to review and
reproduce](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/29).
Help with small, testable tasks such as documenting a branch's entry points,
replacing a hard-coded test path with a synthetic fixture, clarifying a format
hypothesis, or identifying a test that is silently skipped.

For original Carbon PC world/index research, see
[issue #28](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/28).
This needs expertise and locally authorized original game inputs.

## How to submit useful evidence

A good PR or research issue includes:

1. **Exact branch/commit and files tested**, not just a V number.
2. **Question or hypothesis**, plus what observation would falsify it.
3. **Source provenance** where legally shareable: game edition/platform,
   whether original or a derived sample, SHA-256 of the local source and
   method of measurement. Hashes establish byte identity, *not* licensed
   provenance or independence by themselves.
4. **Synthetic reproduction** and a narrow Python test command runnable
   without the original game.
5. **Actual result** with tests run and tests skipped clearly separated.
6. **Limits:** distinguish candidate framing, offline format compatibility,
   loader ABI and true in-game render/physics observations.
7. A statement that no original copyrighted bytes or private local paths
   were included.

When using a source file privately, **never** share the original EA
executables, BUNs, ELF files, texture packs, chunks, copyrighted meshes,
voice/audio content or private file paths. Generated reports should be
reviewed for sensitive path strings before upload. Synthetic fixtures or
brief derived metadata are preferred for collaboration.

## Review and merge expectations

- Draft PRs are **research branches**, not an approved release. Many are
  dependent on another draft PR or propose alternative hypotheses.
- Document source-data assumptions. Keep physical game installation and
  execution separate from analysis. Never introduce an executable patch,
  installer, hook, serialized scene writer or automatic game-file overwrite
  in an ostensibly read-only research PR.
- Prefer small units with explicit failure cases, bounds checks,
  SHA guards, deterministic output, and asset-free CI.
- Use original game tests only on your own locally supplied inputs.
  Never commit those inputs to the project.
- Evidence of an indexed address, a mapped PE section, or an SDK structure
  does **not** alone prove serialized Carbon ABI or gameplay runtime behavior.
- We do not merge draft stacks automatically. Maintainer review and
  source/licensing review come first.

## A realistic milestone order

**M0: source-only reproducible research baseline.**
New collaborators can clone and run synthetic tests from a reviewed branch.

**M1: authenticated original Carbon PC world/master structure.**
At least two independently checked original scene ROOTs, no false
`0x34110` assumptions, and independently traced loader/index ownership.

**M2: one observed in-game object.**
In a separate test installation, load one legal known-good PC resource,
then demonstrate one Undercover model rendering with the correct object
identity, material/texture and scenery placement. Include versioned
logs/screenshots and say exactly what was seen. A loader call succeeding
without rendering does not meet this milestone.

**M3: collision and a small drivable road section.**
Only after world registration and first rendering have real evidence.

The project's complete-port horizon is unknown. Finishing one honest
vertical slice is more valuable than inflating the version count.

## Coordination

Before starting large work, comment on [issue #28](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/28)
or [issue #29](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/29)
and identify which draft PR/branch you plan to build on. That helps prevent
two incompatible analyses being labeled with the same version.
