# V106: public Wii SDK configuration path provenance

Independent, read-only SHA-authenticated DOL/ELF metadata check.
This reports only bounded counts of allowlisted public SDK path
literals inside original initialized *data* sections. It never
uploads original game files, prints byte dumps, or logs proprietary
game strings. An absent known literal is not proof of a missing
configuration file: a path may be assembled dynamically. Likewise,
a present literal does not prove that the reduced native fixture
initialized the real guest pointer. Use these counts to guide the
next original SC initialization restoration, not to fabricate a
successful IOS_OpenAsync response.
