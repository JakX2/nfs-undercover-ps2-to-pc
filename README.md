# NFS Undercover PS2/Wii → Carbon PC

Research repository for an **offline, native-format porting investigation**. This is **not a playable PC port**.

Current published-research baseline: V41 native scenery model conversion and V43–V46 scenery spatial/opaque-chunk analysis. The original Carbon PC world stream and in-game runtime behavior are not yet verified.

**V15 Carbon loader evidence:** The read-only [original resource control chain](research/world_bridge/CARBON_PC_ORIGINAL_CONTROL_CHAIN_V15.md) correlates a single XNFSModFiles.txt entry, one owner-private native Carbon PC resource, and the exact-path NFSC.exe ProcMon capture, with synthetic original-free regression tests. This is an evidence gate for a controlled test, **not proof that Carbon registered or rendered external assets**.

Original game files, extracted binary data, textures and models are **not distributed** in this repository. All research scripts operate on game files supplied locally by the user. Do not install experimental outputs into a live game.

See the research-source pull request for the source-only Python tools, test infrastructure and evidence reports.
