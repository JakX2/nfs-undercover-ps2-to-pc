# V1310: cooperative context mapping boundaries

Require every saved context word to remain mapped at the initial provenance snapshot, rather than assuming endpoint mapping proves all interior words. Separately validate the OSThread.state halfword just beyond the OSContext extent before selection. Add two original-free unmapped-memory cases. No guest state changes; original V1308 owner retry remains pinned. CI pending.
