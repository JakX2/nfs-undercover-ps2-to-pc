# V1153: correct synthetic held epilogue context

The V1151 live fixture initially used the owner context constant instead of the independent V997 fixture address. All eight new modes correctly failed at the same-tick admission. Use the fixture's own v958::context in the new synthetic metadata. No runtime ownership requirement is relaxed. The workflow now triggers on edits to this fixture. V1150's 368 independent synthetic cases passed before this change. Rerun pending.
