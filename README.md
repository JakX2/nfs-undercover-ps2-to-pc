# NFS Undercover PS2/Wii → Carbon PC

Research repository for an **offline, native-format porting investigation**. This is **not a playable PC port**.

Current published-research baseline: V41 native scenery model conversion and V43–V46 scenery spatial/opaque-chunk analysis. The original Carbon PC world stream and in-game runtime behavior are not yet verified.

**V15 Carbon loader evidence:** The read-only [original resource control chain](research/world_bridge/CARBON_PC_ORIGINAL_CONTROL_CHAIN_V15.md) correlates a single XNFSModFiles.txt entry, one owner-private native Carbon PC resource, and the exact-path NFSC.exe ProcMon capture, with synthetic original-free regression tests. This is an evidence gate for a controlled test, **not proof that Carbon registered or rendered external assets**.

**V16 PC resource-stream audit:** [Carbon BUN chunk stream analysis](research/world_bridge/CARBON_PC_BUN_CHUNK_STREAM_V16.md) now checks complete, bounded top-level resource framing instead of assuming a single eSolid or texture root. It also checks duplicate model/texture identities across roots. The combined V15 loader-control tool uses this stricter full-file validation; it is still **offline evidence only**, not proven loader compatibility or in-game rendering.

**V17 calibrated external-loader test:** The new [Carbon A/B/A capture gate](research/world_bridge/CARBON_PC_EXTERNAL_ABA_CAPTURE_V17.md) compares baseline, enabled-resource and restored Carbon runs against the same original Carbon file. It also requires a normally accessed stock game file to be observed in each ProcMon capture, reducing false conclusions from missing events. This is **filesystem evidence only**, not confirmed resource registration or rendering.

**V18 combined Carbon runtime-evidence gate:** The new [joint file-read and reversible screenshot test](research/world_bridge/CARBON_PC_EXTERNAL_ABA_VISUAL_JOINT_V18.md) checks whether a calibrated A/B/A external resource read coincides with a localized pixel change that disappears after restoring the original game state. It is a redacted, read-only experimental control, **not proof that Carbon registered or rendered any particular Undercover asset**.

Original game files, extracted binary data, textures and models are **not distributed** in this repository. All research scripts operate on game files supplied locally by the user. Do not install experimental outputs into a live game.

See the research-source pull request for the source-only Python tools, test infrastructure and evidence reports.
