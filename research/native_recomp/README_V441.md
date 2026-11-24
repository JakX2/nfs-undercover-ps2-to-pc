# V441: Windows OS-time continuation with corrected native ticks

V436 authenticated Windows run 45316760178 passed strict DOL equivalence,
reload, data, DBInit and OSInit entry, with zero fallback and exit zero.
V438 pinned run 45318247837 passed native baseline and corrected loop,
mid-loop resume, linked call and linked-call resume on both output modes.
The Windows full-image default is now os-time (V435 Linux verified).
The independently validated label-tick fix is enabled by default, with
--legacy-ticks and the matching workflow input retained as controls.
The synthetic byte-reverse control also uses the corrected emitter.
The owner-original Windows OS-time execution remains pending CI.
