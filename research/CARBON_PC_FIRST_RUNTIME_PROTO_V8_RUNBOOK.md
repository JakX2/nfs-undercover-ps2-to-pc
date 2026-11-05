# V8: Windows prototype doctor + single-entry runbook

**Date:** 2026-11-05. **Target evaluation date:** 2026-11-07. **State:** source-only, original-binary static observations; no retail Carbon gameplay test.

## What's genuinely new

- `uc_carbon_proto_v8_doctor.py` is a **read-only** audit of Python, the 15 locally required source modules from draft PR #33, the original installed Carbon `TRACKS/L5RB.BUN` **and** `TRACKS/STREAML5RB.BUN` fingerprints, and the original PC executable's embedded RB pathname strings. It never modifies the installation. The old V7 checker validated the installed stream only; V8 additionally detects a different or modified installed **BUN index file**, which could defeat the proposed image-span test.
- `Invoke-CarbonPrototypeV8.ps1` is one PowerShell entry point for the existing V7 `check`/`stage`/`prepare` and PR #33's guarded `install`/`restore`/`status`/`evidence`. Default action is `Doctor`, not installation. Private file creation and installation actions need explicit switches; `Install` and `Restore` require **both** `-ConfirmWrite` and `-GameClosed`, and the existing guard rechecks `NFSC.exe` process status. It does **not** launch the game or inject code.
- `PRIVATE_CONFIG_TEMPLATE.json` is a template with **fictional paths**. Keep your customized private copy **outside** both GitHub and the game directory; it exposes private filesystem paths. Do not share the private config, original game files, edited streams, session backup, ProcMon CSV, or gameplay screenshots.

Original-source static check: the user-supplied Carbon PC `NFSC.exe` (7,217,152 bytes, 32-bit Windows PE) contains the literal path strings `TRACKS\L5RB.BUN` and `TRACKS\STREAML5RB.BUN`. This suggests a loose RB path is recognized by this executable; it is **not** evidence that it actually opened or rendered from either file. A public [SteamDB Carbon file manifest](https://steamdb.info/depot/3628292/subs/) independently lists both loose RB files, including a `STREAML5RB.BUN` of 79.00 MiB. A different Carbon release or modded install may not match the owner's audited hashes; the V8/V7 pin intentionally refuses it.

## What you need on your Windows Carbon PC

Python **3.11+**, a complete checkout of the draft PR #33 `research/ps2-map-swap-as-pc-port-oracle` branch, an installed Carbon PC with `NFSC.exe` and loose `TRACKS/L5RB.BUN` + `TRACKS/STREAML5RB.BUN`, original pristine RB files extracted from the owner's Carbon PC split archive, and the owner's original Undercover PS2 `TRACKS.zip`. For staging and backup, reserve at least **300 MiB** private free disk space outside the game tree; more space is prudent. All files must be legitimately supplied from the owner's installations/media.

Copy all **V7 + V8 Python scripts** and this PowerShell runbook into the same private working folder. Copy `PRIVATE_CONFIG_TEMPLATE.json` to e.g. `D:\PrivateProto\PRIVATE_CONFIG.json` and edit it with your own existing private paths. `world_bridge_dir` must point at the **complete** source directory from PR #33, not the minimal ZIP contents.

### Recommended exact sequence

All commands below are PowerShell commands run in the folder where `Invoke-CarbonPrototypeV8.ps1` is located. Use your **private** config path, not the template. Each action is separate and stops on the first failure. Avoid using `Set-ExecutionPolicy` globally; if PowerShell blocks the script, review your machine's script execution policy locally.

```powershell
$config = 'D:\PrivateProto\PRIVATE_CONFIG.json'

# Day 1: never changes the game, checks all source scripts and BOTH installed RB files.
.\Invoke-CarbonPrototypeV8.ps1 -Action Doctor -ConfigPath $config
.\Invoke-CarbonPrototypeV8.ps1 -Action Check -ConfigPath $config

# Day 1/2: user-controlled NEW private stage and separate full original backup.
# Close Carbon first, and never reuse existing stage/session paths.
.\Invoke-CarbonPrototypeV8.ps1 -Action Stage -ConfigPath $config -ConfirmWrite
.\Invoke-CarbonPrototypeV8.ps1 -Action Prepare -ConfigPath $config -ConfirmWrite

# Day 2: AFTER capturing the stock game image and fully closing NFSC.exe.
# This alone explicitly opts in to replacing only the loose installed RB STREAM.
.\Invoke-CarbonPrototypeV8.ps1 -Action Install -ConfigPath $config -ConfirmWrite -GameClosed

# USER ACTION: launch Carbon normally, attempt to navigate to a scene using the
# targeted material, capture staged screenshot and optional Process Monitor CSV.
# The material/camera location is not guaranteed by offline source geometry.
.\Invoke-CarbonPrototypeV8.ps1 -Action ReadEvidence -ConfigPath $config

# Exit Carbon, restore the exact original stream, confirm status, then recapture.
.\Invoke-CarbonPrototypeV8.ps1 -Action Restore -ConfigPath $config -ConfirmWrite -GameClosed
.\Invoke-CarbonPrototypeV8.ps1 -Action Status -ConfigPath $config
.\Invoke-CarbonPrototypeV8.ps1 -Action VisualEvidence -ConfigPath $config
```

**ReadEvidence runs while the staged stream remains installed.** Run `VisualEvidence` only after collecting the third screenshot (`restored.png`) after restoration. The existing screenshot validator requires a private ROI worksheet with target and background rectangles; see `CARBON_PC_PRIVATE_VISUAL_ABA_EVIDENCE_GATE.md` in the draft branch. Process Monitor CSV and screenshots are optional tools for evidence, but a credible first visible prototype requires actual game screenshots and reproducibility. A real in-game test cannot be performed by this Linux-side source build.

### What counts as a pass

- V8 `Doctor` returns `READY_FOR_V7_CHECK_NOT_RUNTIME_PROOF` on Windows with matching installed RB files and a complete source checkout.
- V7 `Check` accepts the user's original Carbon/Undercover source files and exact 142/DXT5/16 ↔ 241/31 donor compatibility. `Stage` modifies *only* an existing image span **in a new private copy**; `Prepare` creates a separate, immutable pristine backup without changing the installed game.
- The game launches after explicit guarded install; the visible before/staged/restored difference localizes to the intended surface while stable background anchors remain unchanged; and original installed stream bytes are byte-exactly restored.
- If there is no visible change, we call it `RUNTIME_BLOCKED_OR_TARGET_NOT_VISIBLE`, **not** a working Undercover-in-Carbon prototype. A ProcMon file read establishes read evidence, not rendering.

### Fast failure diagnosis

| Symptom | Meaning / action |
|---|---|
| `BLOCKED_INCOMPLETE_OR_INCOMPATIBLE_SOURCE_TOOLCHAIN` | The full PR #33 `research/world_bridge` Python directory isn't present, or a required file doesn't parse / has a mismatched API. Clone/download the actual draft branch, not just V7/V8. |
| `BLOCKED_MISSING_LOOSE_RB_GAME_FILES` | Installed Carbon doesn't contain the loose files this test safely replaces. Stop rather than adding guessed overlay/override paths. |
| `BLOCKED_INSTALLED_RB_DIFFERS_FROM_AUDITED_ORIGINAL` | Another game version or mod may be installed. Don't overwrite or disable fingerprint checks; use the matching pristine source/install for this experiment. |
| Python `ModuleNotFoundError` | Check `world_bridge_dir` and that the full branch files are checked out. V8's static completeness check catches the known dependency chain, but later dynamic imports can introduce more. |
| Python launcher/version error | Set `python_executable` to the full path of the desired Python 3.11+ interpreter, or an executable available on `PATH`. |
| `NFSC.exe is running` | Close Carbon completely, including background processes, before explicit installation or restoration. |
| Failed `ReadEvidence` | A missing/incorrect Process Monitor CSV or no verified staged stream can cause refusal; screenshot testing can still be performed after a correctly staged game session, but cannot claim byte-range read proof. |
| No visible texture change | Could be wrong travel location, streaming, cache, alpha blending, a different resource identity or loader behavior. Restore, keep evidence, and investigate; do not patch arbitrary pointers. |

## Validation scope

V8's Python doctor has **27 independent synthetic tests**. The bundled V7 wrapper has **28 synthetic tests**, for **55 combined local tests**. Source-only tests exercise no original game assets and no actual Windows file replacement. The PowerShell runner is **reviewed statically**, not executed here because no Windows/PowerShell environment is present. This is a preparation kit, **not a working Carbon PC build**.