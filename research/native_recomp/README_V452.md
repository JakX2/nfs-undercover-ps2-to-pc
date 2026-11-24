# V452: localize the next nested NAND repair rejection

Authenticated owner workflow 45322037051 reproduced the V437 five-entry
route: four original entries, fifth NOP, two nested calls, no BLR/resume.
The V447 source tests passed; the owner plan failed before regeneration.
The previous outer workflow published only the failed-stage label.

V452 retains every V447 original-byte and AOT entry/dispatch constraint.
It separates the private plan checks into fixed categories and stable
entry ordinals. Entry trace and fallback dispatch presence are reported
as booleans only; no address, opcode, private path or exception text is
published. The normal successful outer workflow now publishes the same
bounded repair evidence as its failure path. New synthetic controls
exercise call order, range, missing entry and missing dispatch.
The exact next repair remains unverified until owner CI.
