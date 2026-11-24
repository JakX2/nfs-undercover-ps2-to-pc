# V566: isolated SC cache patch composition

V565's original-free SC workflow (45431751744) stopped during patch installation, before generation. The shared V43 CPU-context anchor assumes HID4 has already been installed, but the focused SC harness uses V18 HID0/HID2 without the continuous HID4 chain.

V566 retains the V43 cache methods and emitter edits, with a separate exact SPRG/BackupState anchor for the pinned isolated runtime. It validates the whole transformation, idempotence, roundtrip, mixed-state rejection, duplicated anchors and absent HID0 before writing. The runner names the failed source-only patch without exposing private generated content.

The owner job remains gated on the independent synthetic job. No SC original execution or boot advancement is claimed until CI verifies it. Full-image cache configuration is unchanged.
