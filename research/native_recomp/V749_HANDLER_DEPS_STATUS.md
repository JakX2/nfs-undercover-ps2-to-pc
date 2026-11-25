# V749: bounded original SI handler dependency graph

V746 owner run confirms exact repeated system-time root, and identifies possible later SI transfer, alarm cancel, public SITransfer and unnamed helper. V749 privately authenticates these four distinct callsites, enumerates their direct/indirect/tail dependencies and conservative pre-call MMIO region counts. Known already-proven roots are classified by exact address equality, not symbol name. No game code, addresses, unfiltered symbols, dynamic path or new execution claims. This is preparatory data for the V747 actual next-boundary result.
