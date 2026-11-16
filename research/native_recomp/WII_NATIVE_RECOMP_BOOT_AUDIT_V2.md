# V2: real Undercover Wii static startup call audit (original-free report)

**Date:** 2026-11-12. This is a read-only *static* PowerPC/ELF analysis of the owner's private, matching `NfsMWRelease.elf` and `NfsMWRelease.dol`. The analysis is **not an execution trace, successful recompilation, native Windows boot or new in-game footage**. No original executable, serialized assets, translated game code, or complete function-name inventory is packaged here.

## Verifiable source and method

- Wii ELF SHA-256 `fd9681f2b06e961667bcad2eea6aaf6c762e0f30d666376d1ebb5f2946455ab0`; Wii DOL SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
- Reuses V1 strict ELF/DOL loaded-section matching (6,432,900 bytes identical), big-endian ELF32 PPC section labels and 27,941 sized named STT_FUNC functions.
- Walks 4-byte words *inside named ELF function spans*, categorizes major PPC opcodes, decodes direct `b`, `bc` branch destinations (AA/LK flags) and indirect `bclr`, `bcctr` sites. Builds a bounded direct-call graph from the ELF `e_entry`.
- A direct-call *edge* is a **distinct caller/callee function pair**, not a callsite count. A depth-3 graph includes all named potential direct callees at distances <=3, not verified runtime calls. Indirect calls, vtables and address-taken callbacks are deliberately not inferred.

## Actual source results

| Gate | Result |
|---|---:|
| ELF / DOL program entry (`__start`) | `0x8000403C` |
| Original Wii game `main` label | `0x802D3F40` |
| Named function starts | **27,941** |
| Four-byte instruction words in named functions | **1,410,536** |
| Percentage of executable section bytes covered by named function spans | **99.8255%** |
| Distinct direct-call graph edges | **55,901** |
| Sites with direct linked-branch destination that is **not** a named function start | **3,235** |
| Of those, targets **inside existing named function spans** | **3,228** |
| Of those, targets **within executable code but outside named spans** | **7** |
| Of those, destinations outside executable sections | **0** |
| Indirect linked branch sites (`bclrl`/`bcctrl` forms) | **13,323** |
| Primary opcode `4` words (paired-single *family*, not verified specific mnemonic) | **754** |
| Direct link branch sites in `__start` | **11** |
| Potential direct-call reachability, depths 0/1/2/3 | **1 / 11 / 71 / 238** (321 total) |

**Important:** the 3,228 interior destinations are not necessarily defects. Many target compiler support routines such as `__save_gpr` and `__restore_gpr`, which intentionally expose multiple entry points inside one symbol. A recompiler must preserve those semantics; blindly labeling each interior target as a new conventional C++ function can break register restore behavior.

### Direct `__start` link targets, in binary order

| Call site | Target | Named symbol |
|---|---|---|
| `0x8000403C` | `0x800041A8` | `__init_registers` |
| `0x80004040` | `0x800042E0` | `__init_hardware` |
| `0x80004054` | `0x80004238` | `__init_data` |
| `0x800040C8` | `0x80004028` | `__set_debug_bba` |
| `0x80004158` | `0x804E5020` | `DBInit` |
| `0x8000415C` | `0x80520670` | `OSInit` |
| `0x80004180` | `0x80004000` | `__check_pad3` |
| `0x80004184` | `0x80004034` | `__get_debug_bba` |
| `0x80004190` | `0x80555F14` | `InitMetroTRK_BBA` |
| `0x80004194` | `0x8052DAEC` | `__init_user` |
| `0x800041A0` | `0x802D3F40` | `main` |

These are **static call sites**, not a claim that they execute in exactly this order on a real Wii (branch conditions can skip some, other functions can abort, and callbacks may intervene).

## Next executable gates

1. Test WiiCompiled generic translation with V1 private manifest and function map, pinned to upstream source commit and original DOL hash. **Capture unsupported instructions and first failing PC**, and classify whether they occur within startup or only in other reachable functions. Do not enable `allow_unsupported_instructions` as a pass criterion.
2. Independently test NWiiRecomp DOL analysis and generated native project. For runtime use `NWII_HEADLESS=1` and `NWII_TRACE_CALLS=1`, then correlate actual logged PC order with the above entry, `OSInit`, `__init_user`, `main`. An emitted C++ file is not boot evidence.
3. Treat 7 unlabelled executable direct-call targets and the interior helper targets explicitly as **mid-function entry/call-dispatch validation gates**, not missing imported libraries by default.
4. Compare startup memory, Wii IOS services, DVD/file loading, MEM1/MEM2 layout, GX, and VI setup to Dolphin traces from the owner's original disc. Do not distribute proprietary assets or game executable.

**Current blocker:** local environment lacks `dotnet`, and network Git clone is unavailable. Neither translator was executed during V2. This report provides the exact original-file checkpoint targets and an original-free reproducible audit script/tests instead.

## Runbook

```sh
# Owner-local only. Put scripts together in research/native_recomp/.
python -m unittest discover -s research/native_recomp -p 'test_*.py' -v
python research/native_recomp/wii_recomp_preflight.py \
  --elf /private/NfsMWRelease.elf \
  --dol /private/NfsMWRelease.dol \
  --output /private/recomp-results
python research/native_recomp/wii_recomp_boot_audit.py \
  --elf /private/NfsMWRelease.elf \
  --dol /private/NfsMWRelease.dol \
  --output /private/recomp-results --depth 3
```

The generated `boot_static_summary.json`, `boot_private_call_targets.json`, `private_function_map.txt` and `undercover-wii-generic.yml` stay private. The static summary contains only aggregate counts and console segment addresses; the private call targets include function labels and must not be published automatically.
