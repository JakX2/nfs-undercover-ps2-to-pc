# NFS Undercover PS2/Wii → Carbon PC

Research repository for an **offline native-format porting investigation**. This is **not yet a playable PC port**.

## Wii PowerPC → native PC physics host (V21, November 11, 2026)

The separate [Wii executable research PR #35](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/35) now builds an **independently authored C++17 physics static library and executable on native Windows and Linux**, without emulation or retail Wii binaries. The synthetic CLI `nfsuc_physics_smoke` composes recovered rigid-body integration, quaternion/matrix updates, aerodynamic drag, end-of-frame force accumulation and base sleeping/Detach behavior. **Both platforms passed native 2-frame and 4-frame CTest checks.**

Build locally with `cmake -S research/wii_executable -B build/wii-native`, `cmake --build build/wii-native --config Release`, then `ctest --test-dir build/wii-native -C Release --output-on-failure`. See [V21 native host build instructions](research/wii_executable/WII_NATIVE_PC_SMOKE_V21.md) and the [Windows/Linux CI workflow](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/workflows/wii-native-host.yml). Successful CI runs may provide precompiled **original-free physics smoke executables**, not a game.

**This is not a playable Undercover PC port.** The executable runs only synthetic rigid-body scenarios. Vehicle steering/suspension, contacts and collision physics, world streaming, graphics, audio, inputs, actual game assets and original Wii runtime equivalence remain to be implemented and validated.

## Original-source world-stream findings

**V6, 2026-11-05:** Carbon PC RB section 299 uses two serialized eSolid header values: 73 solids with `0x00000016`, and four with `0x00400016`. The version-aware offline reader verifies all 77 indexed identities and six post-scene group matches. Across seven RB sections, **20/20** `0x37250` record groups have identical model-hash candidate fields at `+0x44` and `+0x4C`, backed by local scenery and solid indexes. This is *not* evidence of pointer semantics or runtime registration.

An independent, bounded scan of 961 Carbon PC RA sections found **no match for the exact RB-specific post-scene sequence**; RA's format must be investigated separately. This is a format-profile negative, not evidence that RA lacks scenery or models.

Read [V6 findings and limitations](research/CARBON_PC_POSTSCENE_V6_VARIANT_AND_RA.md) and the earlier [V5 original-source controls](research/CARBON_PC_POSTSCENE_ORIGINAL_RB_V5.md).

## Prototype experiment: November 7, 2026

A source-only [V8 Windows prototype readiness runbook](research/CARBON_PC_FIRST_RUNTIME_PROTO_V8_RUNBOOK.md) documents a 55-test V7/V8 handoff for a reversible Undercover PS2 texture-in-Carbon PC test. V8 verifies both installed RB files plus required Python dependencies before staging; any installation and restoration require explicit owner-controlled actions.

The owner launched Carbon PC with the staged Undercover texture stream and restored the original afterward. **No imported texture was visibly verified**; no in-game imported model or playable port has been established.

## Undercover scenery material coverage: V9 (2026-11-05)

A read-only owner-original audit reproduced **268 PS2 eSolid occurrences and 76,348 triangles** across eight geometry packs. **46/48** texture identities actually used by Undercover RB scenery have indexed images in the source RB packs. A stricter external-bank scan found **none of the two remaining identities in fully validated PS2 texture indexes** within Undercover `GLOBAL`, `FRONTEND`, `CARS`, or `Unknown`. The car bank uses unsupported image layouts in this specific parser, so this is **not a global absence claim**. Prefer the six fully image-backed source geometry packs when preparing a constrained offline native-asset test; no in-game world import has been proven.

See [V9 source-bank audit](research/UNDERCOVER_PS2_EXTERNAL_MATERIAL_IMAGE_V9.md). The standalone Python V9 scanner and 35 synthetic tests are delivered in the separate source-only research kit.

## First source-backed scenery candidate: V10 (2026-11-05)

A private read-only Undercover PS2 RB audit selected **section 241, geometry pack 0, model ordinal 6 (zero-based)** as an 8-triangle, one-texture, scenery-referenced offline geometry candidate. A larger **144-triangle** candidate is section 241 / pack 0 / model ordinal 42. These are source asset ordinals, not proven Carbon PC scene objects.

The new [V10 gate](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/ps2-map-swap-as-pc-port-oracle/research/world_bridge/UNDERCOVER_PC_FIRST_MODEL_V10_GATE.md) resides in draft PR #33. Its single-model PC-shaped geometry/DXT5 candidate, strict full-table texture closure and native parser tests passed a **1,560/1,560** clean-checkout synthetic suite. **The V10 end-to-end converter has not yet been run on these original candidates or verified in Carbon PC.** See the [source-backed selection report](research/UNDERCOVER_PC_FIRST_MODEL_SOURCE_V10.md).

## V11 original model and external-bundle loader research

Owner-original Undercover PS2 model data was decoded into two **PC-shaped offline geometry candidates**, preserving **8/8** and **144/144** original XYZ/UV/material triangles. The 144-triangle candidate has 288 source vertex samples, one backed material identity and 11 original VIF strips. An external Carbon resource-loader candidate (XNFSModFiles) was also checked statically against the owner's original PE32 `NFSC.exe`; five documented addresses map to executable code. **No native Carbon model registration or rendering has been verified.** See [V11 original-source geometry and external-loader evidence](research/UNDERCOVER_PC_V11_ORIGINAL_MODEL_AND_LOADER_PREFLIGHT.md).

The optional source-only V11 OBJ preview implementation and PE compatibility preflight are in [draft PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33). GitHub Actions has passed **1,604/1,604** synthetic tests on the draft branch. The offline preview can display owner-generated geometry locally but does not make Undercover playable in Carbon.

## V12 native eSolid header controls: 205 exact PC matches

A **209-model original Carbon PC ↔ Carbon PS2 same-identity comparison** found a minimal PS2 header transform: zero the high 16 bits of the word at normalized eSolid offset `+0x14`. That yields **205/209 byte-identical native Carbon PC headers**. The four exceptions differ only in a special PC version flag and remain explicitly unsupported. The transform changes only **1 or 2 bytes** in the two selected original Undercover model headers while retaining complete offline PC-shaped geometry readback for **8/8 and 144/144 faces**. **No loader or game-side model rendering is proven.**

The opt-in transform and tests are in [draft PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33); the complete synthetic CI suite passed **1,626/1,626 tests**. Read the [V12 original-source controls and limitations](research/UNDERCOVER_PC_V12_NATIVE_ESOLID_HEADER_CONTROL.md).

## Research code and work in progress

[Draft source-only research PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33) hosts the broader experimental world-bridge code and tests. The separate V6 version-aware parser is included in the downloadable V6 research kit, not yet committed to that PR. The public V6 report is aggregate-only.

Next: establish a safe Carbon native resource load, then registered single-model geometry plus texture identity, scene references and visibility. Four section-299 special eSolid header versions remain distinct and are not automatically mapped from PS2. RA's distinct section layouts remain a separate research workstream.

Earlier work includes V41 native scenery conversion and V43–V46 scenery spatial/opaque-chunk analysis. All are offline format-research milestones.

## Distribution and runtime boundaries

No original game files, extracted asset payloads, models, textures, executable patches or modified retail archives are distributed here. All game-source analysis uses privately supplied originals.

**No Undercover gameplay, native in-game rendering, world streaming, collision or driveable PC build has been verified.**
