# V1221: authenticate original interrupted instruction resume

Re-derive the exact original startup resume label and split dispatcher mapping, preserve the pre-tick V616 trace and the old V922 observer, and redirect only that existing observer while the held third ACK route is active. The audit requires the complete original final RFI chain and exact two-tick resume. No guest instruction replaced or executed past the frontier. CI pending; continuous predecessor gated.
