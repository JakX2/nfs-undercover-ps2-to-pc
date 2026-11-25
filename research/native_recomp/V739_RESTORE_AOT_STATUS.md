# V739: generated restore alias integration regression

The V734 generated handler-return program is extended independently with a real 15-load native leaf, one deliberately clobbered nonvolatile register, and a separate saved-register frame. Installs the same V738 runtime hooks and native alias instrumentation. Both compilation modes must retain earlier ACK/leaf tests, restore all 15 registers and return to the dispatcher; corrupt LR, corrupt saved GPR and disabled restore-route controls must refuse. No original code is contained in this fixture. CI pending.
