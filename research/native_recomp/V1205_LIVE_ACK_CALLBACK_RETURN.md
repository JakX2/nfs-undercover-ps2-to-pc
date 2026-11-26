# V1205: live callback register restore and caller return

Reuse the existing original outer-dispatch hook and exact resume tick. Validate stack unwind, LR reload, preserved ABI and cleared PI; stop before the next handler instruction. Two synthetic registers in the live fixture, six in the private original metadata alias. One positive and twelve negative live cases. Original private admission not yet enabled; CI pending.
