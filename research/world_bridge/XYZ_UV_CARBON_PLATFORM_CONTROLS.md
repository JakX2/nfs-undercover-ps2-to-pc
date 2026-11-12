# Carbon PC / PS2 XYZ + periodic UV source controls

**2026-11-03. Read-only original-source audit.** Uses the owner's Carbon PC split-TRACKS archive and Carbon PS2 TRACKS archive, both retained privately. Only original analyzers, synthetic-only tests, and aggregate counts are published. No model, image, VIF payload, UV map, proprietary resource hash inventory, executable patch or game archive is committed.

## Reproduce

From repository root with the original files held locally:

```sh
python research/world_bridge/uv_attribute_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --xyz-tolerance 0.01 --uv-tolerance 0.01

python -m unittest discover -s research/world_bridge -p 'test_xyz_uv_spatial_match.py' -v
python -m unittest discover -s research/world_bridge -p 'test_uv_attribute_control.py' -v
```

This extends the previous **132/132 matching Carbon model-hash control** and **114,701/114,701 one-to-one geometric triangle matches**. The control walks native PC 36-/52-byte vertex buffers with mesh-range checks, and genuine PS2 VIF strips with ADC/header validation; it obtains candidate float32 PC UVs from vertex +0x1C and signed 16-bit PS2 ST UV values scaled by 1/4096.

The **pure standard-library** `xyz_uv_spatial_match.py` then requires a source vertex to have a target in the **same model hash** whose XYZ Euclidean distance is at most **0.01 game units** and whose UV Euclidean distance is at most **0.01 after reducing U and V differences by integer tile offsets**. It searches bounded adjacent XYZ spatial cells; the match must satisfy *both* coordinate predicates for **one witness vertex**, not two unrelated targets. Both PC→PS2 and PS2→PC directions are checked. A UV-tile rescue is counted only when there is no same-position candidate with sufficiently close *raw* UV values, but there is a valid periodic UV witness.

## Original archive results

| Source-matched Carbon RB section | Paired solid IDs | PC vertices with XYZ+periodic UV witness in PS2 | PS2 vertex occurrences with XYZ+periodic UV witness in PC | Required periodic U/V tile rescue (PC / PS2) | Largest periodic UV witness distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| **141** | 29 | **99,216/99,216** | **100,464/100,464** | 146 / 156 | **0.0020716** |
| **142** | 103 | **86,610/86,610** | **104,539/104,539** | 120 / 96 | **0.0017606** |
| **Total** | **132** | **185,826/185,826** | **205,003/205,003** | **266 / 252** | **0.0020716** |

No source vertex is unmatched in XYZ or periodic UV in either direction. The maximal selected wrapped UV witness distance is **0.002072**, comfortably under the explicitly declared 0.01 UV tolerance. PC source records and PS2 strip vertex occurrences are not in equal cardinality, because the PS2 stream can repeat vertices and split sections into many strips.

Without integer tile wrapping, the PS2→PC check finds **204,751/205,003** UV witnesses (252 failures), and the PC→PS2 check finds **185,560/185,826** (266 failures) within 0.01. The periodic check resolves *all* those particular differences. That is evidence of whole-number U/V offsets, but **does not prove the game actually uses wrap sampling on all corresponding textures**; a texture address mode must be verified independently.

An exploratory SciPy `cKDTree` UV-distance analysis also found complete two-way periodic UV coverage on the original data. The committed spatial checker uses **no SciPy**. It records upper bounds from selected valid witnesses, not true global minimum distances.

## What this proves and what remains open

**Supported by real source data:**
- Candidate 36-/52-byte PC vertex float32 UV fields and the PS2 VIF signed ST UV fields encode **matching per-model UV values modulo integer U/V tile offsets**, given nearby matching XYZ positions.
- The correspondence is **bidirectional for every source vertex record** in 132 matched Carbon PC/PS2 models across the two selected original RB scenes.
- Severe UV misinterpretations, e.g., a global V flip without compensation or an unrelated UV set, fail the new tests.

**Not established:** equal per-triangle UV winding/corner assignment, per-face material IDs, texture archive or texture atlas equivalence, sampler wrap/clamp modes, tangent-space or normal-map equivalence, identical source vertex multiplicity, a PC vertex writer, Carbon PC model loader acceptance, in-game rendering, collision, traffic or a playable Undercover import. **A periodic vertex-UV match is necessary but not sufficient for identical texture appearance.**

## Verification

**18/18 new synthetic-only tests passed locally** (12 spatial/periodic/malformed controls plus 6 same-hash integration gates). The genuine **132-model original-file audit completed twice**: with a small local SciPy exploratory matcher and with the new pure-stdlib checker wired through minimal compatibility adapters for existing project helpers. These adapters were private inspection aids, not game asset conversions. **All four GitHub source/test blob SHAs match the locally tested copies exactly.** A clean-checkout GitHub CI run has not yet been performed and should not be implied.

## Next falsifiable milestone

Using the established **one-to-one geometric triangle assignment** for two independent original Carbon PC/PS2 control solids, compare **ordered face-corner XYZ+periodic UV attributes** and the matching PC mesh-material chunks versus PS2 strip group/texture identifiers. Identify any mirrored, tiled or repeated material seams and distinguish ambiguity from true source differences. After source-backed face/material controls pass, develop a **reversible synthetic-only 36-byte PC mesh writer**, with strict bounds and no automatic changes to game files.

All owner-provided original files remain unchanged and private.
