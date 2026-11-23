# Authenticated Undercover Wii NAND/ISFS return progression (V398–V403)

## Established original-game execution

All evidence below comes from the separately authenticated, private owner
Wii PowerPC AOT run. None of these milestones means the game has booted.

- **V396–V397:** Sixteen complete 24-call original guest successor traces
  after a genuine NAND IOS reply and dynamically selected
  `_isfsFuncCb` nested callee.
- **V398:** Saved selected-callee LR was observed naturally as the PPC
  `CPUContext.pc` during callback dispatch, in mapped guest code, before
  the 24-call cap. Owner workflow
  [45272006977](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45272006977).
  These are **aggregate** boolean observations, not one per trial.
- **V399:** Each of sixteen trials observed the selected-callee saved PC
  followed by a genuine call originating within `_isfsFuncCb`.
  `site_trials=16 mapped_trials=16 isfs_after_trials=16
  parent_after_trials=16 ordered_trials=16`.
  Owner workflow [45274042376](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45274042376).
- **V400:** Each of sixteen trials next observed the natural PPC PC at the
  parent callback return site `0x805192AC`, followed by a genuine
  parent-origin guest call.
  `site_trials=16 mapped_trials=16 selected_first_trials=16
  parent_after_trials=16 ordered_trials=16`.
  Owner workflow [45274934445](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45274934445).
- **V401:** The saved selected-callee return-PC minus four did **not**
  classify as a recognized PPC linking branch in any of sixteen trials:
  `kind5=16 direct_match_trials=0`. Likewise V400's parent
  linking-opcode check observed `linked_trials=0`.
  Owner workflow [45276015068](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45276015068).

The ordered return-PC observations are real. They do **not** identify the
exact PPC `blr` that executed or establish the semantics of every caller's
LR; a nonlink tail branch or different valid calling convention may be
involved. Do not guess a linking opcode or replace the actual guest PC.
V403 classifies original LR, CTR, stack, and nonlink opcode families to
investigate this negative evidence without exposing the original words.

## Independent extended original-game candidate

V402 recompiles the same private translated Wii executable into a
**separate** 48-call experimental native harness. The authenticated V401
24-call baseline and V403 diagnostic path remain independent. V402
source-transform, compiler, link or guest-abort errors are specifically
classified, not silently passed as extended execution. A V402 experiment
is **not** a 48-call milestone unless its own authenticated census reports
the number of completed original guest trials. The original 24-call
success must remain green even if this more distant candidate fails.

## Verification and privacy

Use the source-only tests for each stage:

```sh
for v in 396 397 398 399 400 401 402 403; do
  python3 -m unittest discover -s research/native_recomp -p "test_v${v}*.py" -v
done
```

The owner runner retains original Wii executables, ELF files, generated
PowerPC AOT source and raw logs **only** in private temporary CI scratch
space. Public diagnostics are bounded flags and counters. No proprietary
game assets, opcodes or translated game-code bodies are committed.
Legacy V295–V298 failures remain visible as separate historical
diagnostics, never substitutes for the authenticated V396+ evidence.

Full native Windows game startup, frontend, rendering and gameplay
are not yet achieved or verified.
