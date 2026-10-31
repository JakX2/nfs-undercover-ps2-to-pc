# V50: Original-Wii scenery preculler cohorts and auxiliary-record invariants

**NFS Undercover Wii/PS2 → Carbon PC native world port | Maps & World Conversion/Geometry**

## Scope and evidence

This offline, read-only milestone analyzes **one SHA-256-pinned original Undercover Wii scenery root** already supplied for the RedBuilding research. It does **not** establish the serialized Carbon PC layout for `0x34103`, `0x34107`, or `0x3410D`, and provides **no writer or installable mod**. A supplied expected SHA verifies byte integrity against the caller's hash, not game/platform provenance, except for the specifically pinned Wii fixture.

Source Wii RedBuilding scene SHA-256: `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`; length **8,488 bytes**.

## New exact-source observations

- `0x34103` contains 31 original 96-byte candidate scenery instances following a 4-byte alignment gap in this scene. Their **signed 16-bit field at instance offset `+28`** has nonnegative values from **0 through 23**, with every one of the 24 possible indices referenced by at least one instance.
- `0x34107` is 3,072 bytes: exactly **24 candidate 128-byte blocks**. Block **0** is entirely zero and is referenced by source instance slots **1, 2, and 30**; blocks **1–23** are populated. This is a structural index-to-block **correspondence**, not a proof of how visibility or culling bits are consumed in a loader.
- The original `XBu_RedBuilding_1b_00` instance at slot **26** references candidate `0x34107` block **20**. This is distinct from its source scenery-info index of **8**. Its original world position remains approximately `(2631.938721, 3261.404541, 199.968338)`.
- `0x3410D` contains **31 × 32-byte** records. Each record can be divided into four 8-byte slots whose *upper 32 bits are zero*. The lower 32 bits of the first three slots are consecutive integers in **all 31 rows**; the fourth low 32-bit value is not decoded. Of the 31 records, **29 are distinct** and one record occurs three times (at slots 0, 1 and 2).
- The `0x34107` first-block zero case is an important guard against a simplistic interpretation of "zero-filled means unused": three original instances reference candidate block 0.

The observed 128-byte cadence and the Carbon PC RTX community's **128-byte in-memory** `preculler_info` structure are consistent in size, and the public RTX code references `preculler_infos[instance->preculler_info_index].visibility_bits[...]`. This is **third-party Carbon PC runtime evidence only**; it does not establish on-disk equivalence, the meaning of the zero block, nor the Wii/Carbon loader's mapping. See the pinned third-party sources:

- [Runtime struct definitions, pinned commit](https://github.com/xoxor4d/nfsc-rtx/blob/252b44b877c207a9a70914d92c31f116ad92a469/src/comp/game/structs.hpp)
- [Runtime culling access, pinned commit](https://github.com/xoxor4d/nfsc-rtx/blob/252b44b877c207a9a70914d92c31f116ad92a469/src/comp/comp.cpp)

## Tool and tests

`v50_scenery_index_crosscheck.py` reads a standalone scenery ROOT or a ROOT at a supplied original BUN offset. It emits a JSON observation report; **it never edits a game file** and will not overwrite a pre-existing output or source path.

```bash
# Run asset-free tests (safe in public GitHub CI):
python -m unittest discover -s research/v50 -p test_v50.py -v

# Optional additional tests using your own ORIGINAL Wii extracted 8,488-byte fixture:
NFS_UC_WII_SCENE=/private/path/UC_Wii_RedBuilding_Original_Scene.chunk \
  python -m unittest discover -s research/v50 -p test_v50.py -v

# Read-only observation using your original fixture:
python research/v50/v50_scenery_index_crosscheck.py \
  --scene /private/path/UC_Wii_RedBuilding_Original_Scene.chunk \
  --expected-root-sha256 cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f \
  --json /tmp/uc_v50_observations.json
```

### Regression results in this environment

- New V50: **24/24** (18 synthetic and 6 original SHA-pinned Wii-fixture tests).
- V43–V46 independently rerun in source distribution: **146/146**.
- V41 separately rerun: **18/18**.
- **Total 188/188 targeted tests** in this environment, not a rerun of all porting branches.
- **Carbon PC original world-stream tests: 0; in-game tests: 0.**

## Next native world milestone

1. Test Carbon PC original scenery roots from the authenticated original PC game stream and compare serialized field offsets and block counts without assuming Wii offsets match.
2. Obtain a second original Wii scene with distinct instance and spatial-node counts to cross-test `0x34107` sizing and index-to-block correlations.
3. Reverse engineer Carbon PC `LoaderScenery` and its active preculler/cull-tree consumer to establish real allocation/relocation/ownership rules.
4. Verify whether the V42 appended building's source preculler index (20) is valid for the *target Carbon donor* and whether source-geometry spatial membership must be rebuilt. A valid numeric index alone is not proof of geographic or visibility correctness.

**Status: offline observational research. No installable native-world writer or runtime validation.**