# V676: preserve fatal refusal markers across chained audits

The V675 fixture's idle RAM alias test initially left a nonzero type command in SI RAM. Restore byte zero before the real type scheduler request. Also retain the bounded V670 and V673 refusal markers in the external, dispatcher and ACK audit chains, so a contradictory success log containing a refusal cannot pass even if its exit status is zero. Add negative audit tests. This is original-free verification hardening, not new original execution.
