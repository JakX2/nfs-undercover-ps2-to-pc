# V437: distinguish restored callback nested calls from a real native return

V432 authenticated execution continued the exact first nested call, then
aborted at V402 with two calls observed. That old posttrial gate requires
the prior selected-return and parent-return milestones. A broad LR region
test can stop on a nested call before either can occur.

V437 preserves the V432 control and creates a separate bounded candidate.
It requires the exact three owner entry observations, the known V402
abort, SHA-pinned DOL/ELF, original selected and first nested function
coverage, and the unique original BLR and caller resume word. The broad
region stop is suppressed only while the witnessed selected frame is
active; the original 192-call cap and all old assertions remain.

Two private generated-code observers check the actual BLR with its
saved LR/SP and the original caller resume label with the same SP.
They do not alter guest instructions, state, IOS replies or dispatch.
The audit reports native return-pair progress and original function
coverage independently of old test completion. Unknown or placeholder
descendants are counted, not claimed to be original.

Local C++20 ASan/UBSan passed one positive, eleven negative controls and
duplicate-stop checks. Python source seams and owner execution are CI
gates. No original-game content is published. This is not a completed
NAND return or game boot until authenticated runtime evidence passes.
