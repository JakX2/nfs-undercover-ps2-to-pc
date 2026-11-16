# V1: Undercover Wii native recompilation preflight (original-free)

**2026-11-12.** This research evaluates the *possibility* of a standalone Windows/Linux port based on the Wii PowerPC program. It does **not** claim that Undercover has been recompiled, linked, booted or rendered. The existing reconstructed rigid-body smoke test in draft PR #35 is a separate original-free program, not execution of the original Wii binary.

## Verifiable input findings

The owner-supplied, private `NfsMWRelease.elf` and `NfsMWRelease.dol` were inspected read-only. These are the same named inputs previously audited in draft PR #35. For local revision pinning only:

| Property | Value |
|---|---|
| ELF32 architecture | Big-endian PowerPC (machine 20), executable, unstripped |
| ELF size | 11,151,296 bytes |
| DOL size | 6,433,280 bytes |
| ELF SHA-256 | `fd9681f2b06e961667bcad2eea6aaf6c762e0f30d666376d1ebb5f2946455ab0` |
| DOL SHA-256 | `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4` |
| Matching executable entrypoint | `0x8000403C` |
| Nonzero DOL code/data regions | 11 |
| Verified loaded ELF section bytes in DOL | 6,432,900 (zero mismatches; remainder zero padding) |
| Named function symbols inside executable sections | 27,941 |
| Unique function start addresses | 27,941 |

Wii startup assembly's `__start` calls `__init_registers` at `0x800041A8`. Examining its `lis/ori` pairs establishes:

- `r13` (`_SDA_BASE_`): **`0x8070E8E0`**
- `r2` (`_SDA2_BASE_`): **`0x80715EE0`**
- `r1` (initial stack pointer, informational): **`0x80751CB8`**

These r13/r2 bases are the exact required values for the **current** WiiCompiled translator's generic-DOL manifest. The function-map names are *not* a guarantee of correct function discovery/translation, runtime state, ABI behavior or target engine portability.

## Reproducible local tool

`wii_recomp_preflight.py` is standard-library-only, read-only toward game inputs, and emits solely **owner-local artifacts**:

- `private_function_map.txt`: ELF-derived `0xADDR fn_ADDR_name` entries for the optional WiiCompiled `translation.function_map.path` setting; function labels are sanitized and prefixed with addresses to avoid duplicate generated identifiers. **Do not commit or distribute this file.**
- `undercover-wii-generic.yml`: WiiCompiled generic translator manifest, pinned to the supplied DOL SHA and observed SDA bases, with `allow_unsupported_instructions: false`.
- `preflight_summary.json`: aggregate counts, input hashes and explicit `toolchain_execution: not attempted`.

Run from a checkout with Python 3.10+ and private game files (substitute actual owner paths):

```sh
python -m unittest discover -s research/native_recomp -p 'test_*.py' -v
python research/native_recomp/wii_recomp_preflight.py \
  --elf /private/NfsMWRelease.elf \
  --dol /private/NfsMWRelease.dol \
  --output /private/undercover-recomp-output
```

The five synthetic-only tests cover valid map/manifest output, corrupted DOL bytes, inconsistent ELF/DOL entrypoints, malformed ELF section tables, and missing SDA initialization. **5/5 passed locally**, and the real input preflight completed successfully. The test fixtures do not embed game data.

## The real gate: translate, compile, boot

Current upstream references (check again before building):

- [NWiiRecomp](https://github.com/BlackLineInteractive/NWiiRecomp), a general Wii/GC PowerPC translator with a headless HLE runtime. Its `nWiiAnalyzer` and runtime are good first candidates for **startup instrumentation**. Upstream has its own **modified MIT license with noncommercial-only restrictions**.
- [WiiCompiled](https://github.com/patchzyy/Wiicompiled), whose [translator README](https://github.com/patchzyy/Wiicompiled/blob/main/translator/README.md) explicitly supports a generic DOL and optional function map. Upstream uses **GPL-3.0**. Its existing complete port and runtime integrations are centered on Mario Kart Wii.

Suggested local WiiCompiled *translation-only* smoke commands after independently building its .NET 8 translator:

```sh
# Export RECOMP_UC_WII_DOL as the path to the owner's private DOL.
# Example, in a Bash shell:
export RECOMP_UC_WII_DOL=/private/NfsMWRelease.dol

dotnet build translator/src/Translator.Cli/Translator.Cli.csproj -c Release
DOTNET_CLI="translator/src/Translator.Cli/bin/Release/net8.0/Translator.Cli.dll"
dotnet "$DOTNET_CLI" info --project /private/undercover-recomp-output/undercover-wii-generic.yml
dotnet "$DOTNET_CLI" translate-recursive 0x8000403C --project /private/undercover-recomp-output/undercover-wii-generic.yml
```

Record the exact upstream commit, translator command/exit code, functions reached and unsupported PPC opcodes. **Do not treat trap-emitting translation as a passing result.** Later `generate-data-init`, `emit-build-shards`, and native compilation must be evaluated independently. A host-executable from generated code still needs a compatible Wii runtime and asset/disc access.

For NWiiRecomp, first prove DOL analysis and translation with an owner-local TOML profile, then run its generated app in `NWII_HEADLESS=1` with `NWII_TRACE_CALLS=1`, recording whether it enters `__start`, `__init_registers`, `OSInit`, `__init_user` and `main`. This is an experiment, **not a passing gate**. Compare against owner-local Dolphin traces.

## Decision criteria

1. **Preflight (passed):** ELF/DOL same-code identity, unique function starts, entrypoint and SDA registers.
2. **Instruction coverage (pending):** no unsupported instruction traps across reachable startup and main-game paths, particularly paired-singles and indirect calls.
3. **Native compile (pending):** generated C++ links into a host executable with a documented hardware-service stub inventory.
4. **Headless startup (pending):** deterministic logs match original Wii initialization order through initial filesystem access or `main`; classify first failure.
5. **First in-game milestone (pending):** file/resource startup, menu input and eventually a displayed scene. Frame correctness and physics require differential checks against Dolphin.

**Unresolved risks:** Wii operating services, MEM2, Wii GX, DSP/audio, Wiimote APIs, DVD/file-system behavior, runtime-created code, callback/vtable discovery, 32-bit big-endian guest memory, PPC floating-point differences, and upstream code/license compatibility. The manifest's 0x01800000 memory span is an initial MEM1 translation setting, **not evidence that the full game's runtime will never need MEM2**.

**Reproducibility boundary:** No original executable, relocated game bytes, copyrighted assets, full symbol inventory, generated game-specific C++ or personal Drive links are included in this PR. Keep the Carbon bridge and Wii physics research as independent workstreams. This preflight is a foundation for a *new* draft port feasibility branch, not a switch of the public `main` objective until boot-stage results exist.
