# V108: authenticated original SC static data restoration

V106 owner scan found one public `/shared2/sys/SYSCONF` literal.
V107 verified that the exact original native `strlen` source pointer
references that initialized literal in the owner DOL, while the
reduced executable fixture contains zeros at the same address.

V108 owner-only probe restores exactly that original initialized
string from the owner DOL into its original guest virtual address,
only after checking pointer provenance, original bytes, guest RAM
range and an empty reduced-fixture input. Neither a path register,
game branch, IOS return value nor callback is fabricated. The
original native string processing and IOS_OpenAsync must execute
on their own; a missing host fixture file remains an IOS error.

V108 is deliberately a data-restoration probe, not an end-to-end
SC initialization or native game boot milestone.
