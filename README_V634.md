# V634: isolated original mapper dispatch and RFI proof

V633 original-free sanitizer controls passed 4 BAT cases and 80 refusals, 8 combined MI cases and 232 refusals. Expanded original V65 run 45498712546 passed all sixteen trials with alternating low/high alarm priorities. Full-image V633 MI link is still running.

Use a small private DOL built solely from authenticated original mapper and three physical trampoline spans. The real generated dispatcher performs the physical/cached transitions. The corrected common witness checks both RFI returns, exact 32 native BAT writes per trial, ABI preservation and all four entry translation modes with varying existing trace counts. Stop at the real caller return before executing unrelated instructions. No guest patch, hardware permission enforcement, complete-image launch or full boot is claimed. Owner isolated proof pending.
