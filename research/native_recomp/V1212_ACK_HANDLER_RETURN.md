# V1212: held third ACK handler return

Reuse the existing handler return witness and exact dispatcher-resume tick. Validate the independently captured handler entry ABI rather than the callback ABI, keep the cleared PI and saved context, and stop before the dispatcher continues. Eight positive and twelve negative cases. Two synthetic restore loads, not the original fifteen. Move the synthetic channel table outside callback code to avoid accidental overlap. CI pending.
