# Cloud Ghidra for the Wii native port

This folder establishes a **source-only, original-free** Ghidra Headless smoke test
on GitHub-hosted ephemeral machines. No software is installed on the owner's PC.

- Ghidra 12.1.3 official release is SHA-256 pinned.
- GameCube/Wii Loader release 1.3.1 (built for Ghidra 12.1) is SHA-256 pinned.
  It includes the PowerPC Gekko/Broadway language definitions.
- The synthetic DOL is **independently authored** and has two miniature guest
  functions and one PowerPC branch/link. It is not a game-code fixture.
- Headless Ghidra imports this DOL with the GameCube loader, verifies the
  Broadway instruction language and exports only function addresses, sizes and
  call targets to a temporary JSON file. The validator requires a real call
  edge from 0x8000403C to 0x80004050.
- The workflow deliberately uploads **no artifacts**, game content, Ghidra
  projects, analysis databases or derived game metadata. Temp files disappear
  with the ephemeral job. GitHub Actions has read-only repository permissions.

## Execution

Pushes to the Ghidra workflow and this directory trigger cloud smoke tests.
Manual GitHub Actions workflow_dispatch can rerun them. Other source changes do
not repeatedly download 570 MB of Ghidra just to recheck unrelated files.

**Privacy boundary:** The current public GitHub repository MUST NOT import the
owner's original Wii DOL or ELF in Actions. The connected Google Drive access
available to ChatGPT does not give GitHub Actions permission to fetch private
Drive items. Do not insert Drive tokens, public file URLs or encoded game
binaries into workflow inputs, secrets, logs or artifacts.

For a future **private** workspace, the same Java headless exporter supports
the argument mode "private"; it does not seed any synthetic functions. Review
private import semantics and save reports only in that private workspace. This
source-only test does NOT prove genuine owner-game startup, translated C++
execution, booting main, frontend or gameplay.

Upstream source:
- https://github.com/NationalSecurityAgency/ghidra
- https://github.com/Cuyler36/Ghidra-GameCube-Loader
