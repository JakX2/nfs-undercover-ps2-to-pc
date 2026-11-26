# V1173: require admitted original ACK label to have a live path

Refuse a pure old guard hook on a metadata-admitted instruction during preparation instead of deferring the failure to execution. Existing conditional ACTIVE+guard forms remain accepted, because the third ACK route owns ACTIVE. Keep guarded metadata fail-closed at runtime. Add standalone and generated-tree refusal controls.
