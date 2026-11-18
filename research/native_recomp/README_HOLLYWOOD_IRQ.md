# Native Hollywood interrupt controller lane

Independent register model for PPC and ARM pending IRQ latches, mask registers, write-one-to-clear behavior and PI IRQ14 cause routing. Explicit scheduler sampling captures mailbox request and ACK/reply levels without inventing CPU interrupt timing. The model provides no guest CPU exception injection, IOS scheduler wake or device-specific undocumented quirks. Tests cover all 32 sources, independent masks, W1C, IPC handshakes and invalid register access. CI pending.
