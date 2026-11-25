# V830: correct original EXI write harness compile boundary

V828 owner job 139046921071 authenticated both complete 159-word original EXI transfer roots and seven-register compiler aliases, and passed native label/edge composition. The harness build failed before execution. Inspection identified a stale `outer_pc` variable from the predecessor fixture; use the actual synthetic caller root H. Add bounded harness line/error class diagnostics for any future build failure, without logging original translated code or compiler source snippets. Retest pending.
