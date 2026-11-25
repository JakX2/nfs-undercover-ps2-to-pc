# V781: verify live queue witness against original alarm code

Reuse the previously successful V754 and V764 private translation routes without modifying their prior tests. The new focused harness observes all five original cancellation cases and three deadline geometries, and verifies the V780 live snapshot, queue link repair, preserved unrelated fields and exact DEC state. Its head path requires actual original system-time return before authenticating the native decrementer write, and corrupt DEC must be refused. Separate matrix lanes for head and non-head cases; both generated modes. Pending owner CI. These are original-code fixtures with synthetic initial RAM, not a live SI-handler alarm call.

## Verified non-head original paths

Owner run 45555202566, cancel job 139006338634, passed in both generated modes. Each mode executed eight valid original cancellation cases (two each inactive, middle, tail and singleton) plus one guarded head timer control. The live queue witness verified the preserved removed-node links and unrelated alarm fields in these four lanes. The separate head-with-successor lane remains pending. V782/V783 extend the native control-flow checks but are not yet verified.
