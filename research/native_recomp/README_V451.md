# V451: preserve queued full-image verification across unrelated commits

GitHub concurrency retains at most one running and one pending run.
V450's Windows-only scope change displaced the queued V449 original
Linux hardware recheck, even though V450 did not request a full Linux
owner launch. Restrict push triggers to shared full-image build inputs,
witnesses, audits, source validators and their tests. The owner selection
also accounts for the directly used register patches and source validators.
Manual scopes and in-progress jobs remain unchanged.

The V439 terminal-census regression covers genuine terminal, nonzero
exit with terminal, missing or duplicated terminal and a prematurely
emitted terminal. A terminal by itself never constitutes success.
This changed hardware test requests the corrected V449 owner recheck.
No new execution claim is made until the authenticated run completes.
