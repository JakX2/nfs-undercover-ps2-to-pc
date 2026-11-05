# V9: Undercover PS2 external-bank material image audit

**2026-11-05 | Research only, original-owner source reads, no native Carbon PC registration.**

## Why this is part of the port

The Undercover PS2 → Carbon PC model conversion already preserves 268 original eSolid occurrences and 76,348 candidate faces in eight source geometry packs. Those models use **48 distinct material texture identities**. The existing Undercover RB image pack indexes supply only **46** of them. Actual Carbon PC native scene registration and loader/runtime support are still unsolved.

This gate tests whether the two previously unbacked material identities actually occur in other **fully validated PS2 `0xB3300000` texture indexes** rather than assuming arbitrary resource bytes represent images. The inspector also accepts separately extracted source-bank directories, matching the owner's local Windows source layout.

## Original-source measurements

The owner-provided Undercover PS2 RB source ZIP (containing CRC-checked `TRACKS/L2RB.BUN` and `TRACKS/STREAML2RB.BUN`) and owner originals `GLOBAL.zip`, `FRONTEND.zip`, `CARS.zip`, and `Unknown.zip` were audited in a private environment. No game file was opened for writing. Private identities, image pixels, model names, byte offsets, and proprietary payloads are absent from this report and from the code ZIP.

| Source / profile | Aggregate result |
|---|---:|
| RB source geometry packs | 4 in 241 + 4 in 3401 = **8** |
| RB indexed model occurrences | **135 + 133 = 268** |
| RB candidate face count from used strip budgets | **38,205 + 38,143 = 76,348** |
| Distinct material texture identities used by source strips | **48** |
| Indexed images in source RB texture roots | **46 distinct** |
| Unresolved RB material image identities before external scan | **2** |
| `GLOBAL` candidate `0xB3300000` markers / strictly validated PS2 roots / distinct validated IDs | **32 / 11 / 365** |
| `FRONTEND` markers / valid roots / distinct IDs | **5 / 2 / 1** |
| `CARS` markers / roots accepted by this *track/PS2 profile* | **186 / 0** |
| `Unknown` scanned extensionless resources / texture-root markers | **4 / 0** |
| Two missing RB material identities found in accepted external image indexes | **0 / 2** |

**Interpretation:** The two identities are **not present in any of the PS2 texture indexes strictly accepted by this particular scanner** in the searched external banks. This is **not** proof that the materials lack an image anywhere in the game. The `CARS` texture layouts and other unsupported/unvalidated records could still resolve them, and special texture/shader semantics are untested. A raw 32-bit hash occurrence in a geometry file is not a verified image identity.

The Undercover geometry/model/face totals independently reproduce the prior source-backed source→PC material audit. The standalone V9 code verifies RB model-index identity and per-strip material indexes, but does **not** independently redo full PS2 VIF face/UV decoding or native Carbon registration.

## Engineering decision for the first native scene attempt

**Keep all eight geometry packs in the source database.** For a constrained, reversible **offline native-asset prototype**, prefer a model from one of the six packs that are already 100% backed by the 46 original source RB images; do not invent a fallback image, discard the 1,950 unresolved triangle occurrences or replace model hashes with Carbon hashes. Even those six packs are *only parser-valid candidates*, not retail Carbon loader-compatible geometry.

The two incomplete geometry packs remain a separate registration/material-workstream. Further work is required on: native Carbon texture header/identity registration, scenery instance registration and post-scene control semantics, coordinate/visibility mapping, actual engine load behavior, and eventually collision/traffic/navigation.

## Usage and privacy

Run from the extracted V9 source-only ZIP with Python 3.11+:

```powershell
python .\uc_material_source_bank_audit.py `
  --tracks-zip 'C:\Users\Dav\Desktop\nfsuc research\UCPS2\TRACKS.zip' `
  --source-banks 'C:\Users\Dav\Desktop\nfsuc research\UCPS2\GLOBAL' `
                 'C:\Users\Dav\Desktop\nfsuc research\UCPS2\FRONTEND' `
                 'C:\Users\Dav\Desktop\nfsuc research\UCPS2\CARS' `
                 'C:\Users\Dav\Desktop\nfsuc research\UCPS2\Unknown'
```

The `--source-banks` inputs may also be original `GLOBAL.zip`, `FRONTEND.zip`, `CARS.zip`, and `Unknown.zip`. The tool never writes game files or generated resources, and prints aggregate counts only. It rejects symlinked/oversize sources and malformed embedded source indexes. ZIP input members are CRC-checked. Original inputs are re-hashed after scanning. **Do not upload raw archives or modified streams to public GitHub.**

The standalone V9 synthetic regression suite passes **35/35** tests, including material-index selection, nested chunk and image-range validation, strict 128-byte 0x11 pixel alignment, false-root rejection, source ZIP/directory handling, private input preservation, and aggregate-report privacy. These tests do not run the Carbon PC game.

**Result: original-source gap is narrowed, but the original Carbon PC game world port remains unplayable.**