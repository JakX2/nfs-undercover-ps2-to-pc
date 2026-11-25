# V945: correct synthetic dispatcher geometry

V944 source-only test aborted because the fake scheduler's nested call instruction occupied its own entry address, overwriting the expected entry word. Separate synthetic call sites from entry labels and add trial/line diagnostics. Runtime witness unchanged. Rerun pending.
