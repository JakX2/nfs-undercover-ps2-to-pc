# V707: native leaf test compile correction and real timebase checks

V705's first compile failed because the fixture's global `index` variable collided with the POSIX string function declaration in CPUContext's includes. Rename it to leaf_index; no runtime change. Verify actual low/high guest timebase outputs against the virtual instruction counter at each native mftb label, starting above 2^32, and require flushed exact result/refusal markers instead of exit status alone. Split/non-split rerun pending.
