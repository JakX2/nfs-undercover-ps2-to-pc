# Run the first shared Carbon research baseline

**This is an asset-free, noninstallable starting point.** It is intended for
contributors who want to reproduce **synthetic** binary-format checks, not
for someone expecting a playable Need for Speed Undercover PC port.

This branch is a **reviewable consolidation proposal**, stacked on the
[documentation handoff PR #30](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/30).
`main` may not contain these files until both PRs are reviewed and merged.

## Run in three commands (Python 3.10+)

```sh
git clone https://github.com/JakX2/nfs-undercover-ps2-to-pc.git
cd nfs-undercover-ps2-to-pc
git fetch origin integration/first-asset-free-carbon-research-baseline
git switch --detach FETCH_HEAD
python -m unittest discover -s tests -p 'test_*.py' -v
python examples/synthetic_smoke.py
```

The first command group installs **no package or external dependencies**.
The Python scripts use only the standard library.

The test run contains **56 synthetic cases**: 30 original format-neutral
chunk-probe cases, 24 static PE32-address-probe cases, and two tests of the
new contributor demo. The demo synthesizes a toy EA-like chunk stream and
a fake Windows PE32 file, checks both through the read-only scanners, prints
a JSON summary, and destroys its temporary inputs. It does not access a
real `NFSC.exe`, original game BUN, texture, mesh or game installation.

**Expected demo facts:** 2 candidate chunk records, 4 old public loader
virtual addresses mapping into executable sections of the *fake* PE32,
`real_original_game_input_used: false`, `carbon_game_runtime_verified:
false`, and `safe_to_install: false`.

## What's in this small baseline?

| File | Reason to keep |
| --- | --- |
| `tools/carbon_chunk_probe.py` | Standalone read-only candidate `0x80034100` / `0x34110` header inventory. Reports ambiguity across byte order and length framing; does **not** assume Wii-specific graph layout or a verified Carbon row schema. |
| `tools/carbon_pe_preflight.py` | Read-only PE32 section mapping of four *historical* Carbon loader addresses recorded in the public XNFSModFiles source. Not a safe hooking or ABI verification tool. |
| `tests/test_carbon_chunk_probe.py` | 30 fully synthetic archive-framing tests. |
| `tests/test_carbon_pe_preflight.py` | 24 fully synthetic toy-PE tests. |
| `examples/synthetic_smoke.py` | A single no-game-files demonstration for onboarding. |
| `tests/test_newcomer_smoke.py` | Ensures the example stays asset-free and accurately marks results as not installable. |
| `.github/workflows/community-carbon-baseline.yml` | GitHub CI reproduces every synthetic test on two Python versions. |

The code is **consolidated from existing project-authored research**, not
new evidence: `carbon_chunk_probe.py` came from
[draft PR #22 V61](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/22)
and `carbon_pe_preflight.py` from
[draft PR #26 V63](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/26).
Test sources were adapted only for the new import paths. No copyrighted
third-party loader code was copied. The older research branches remain
intact, and their test totals should not be added to this branch's totals.

## Optional privately run probes

Once you have your *own authorized original* Carbon PC archives, the
read-only chunk scanner can generate a metadata-only local report:

```sh
python tools/carbon_chunk_probe.py \
  --archive /private/path/to/original/stream.bun \
  --expected-sha256 YOUR_INDEPENDENTLY_MEASURED_64_HEX_SHA256 \
  --report /private/research/chunk_inventory.json
```

For original PC executable **static mapping only**:

```sh
python tools/carbon_pe_preflight.py \
  --executable /private/path/to/original/NFSC.exe \
  --expected-sha256 YOUR_INDEPENDENTLY_MEASURED_64_HEX_SHA256 \
  --report /private/research/pe_preflight.json
```

Never upload game executable/archive bytes, extracted chunks, converted
copyrighted assets or private path manifests. Reports are metadata-only but
should still be reviewed before publication. SHA guards establish byte
consistency, **not independent game provenance**.

### Important: this is not an approved patch

Even if all historical loader addresses map into an executable PE section,
we have **not** verified the actual instruction bytes, function calling
conventions, supported executable edition, resource loader behavior, master
index, geometry registration, materials, collision or world streaming.
`safe_to_install` is not asserted by either scanner. The third-party
2017 XNFSModFiles loader has unreviewed fixed hook locations and unsafe
text parsing: **do not install it unchanged as a compatibility test**.

A useful next contribution is to review this small baseline, then tackle
[issue #28](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/28)
(original Carbon world/master evidence) or
[issue #29](https://github.com/JakX2/nfs-undercover-ps2-to-pc/issues/29)
(contributor-friendly consolidated tooling).

No repository-wide license has been selected; source redistribution terms
need the maintainer's explicit decision before broader reuse.
