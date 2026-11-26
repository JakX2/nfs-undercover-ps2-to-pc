# V1151: live pending epilogue binding

Use the actual retained device controller and PI atomics, not externally supplied state. Route the held epilogue before queue sampling, preserve one owner, return true only at the pending RFI admission and false at the outer poll. Stop at newly saved dispatcher entry. Eight live synthetic scenarios, one valid and seven refusal controls. Private generated metadata and installer not yet enabled. CI pending.
