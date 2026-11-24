# V611: compile-test the generated nested arena expectations aggregate

V609 original-free observer and scope tests passed. Local compiler reproduction found the private header's nested std::array aggregate form lacked one brace level. Replace ambiguous aggregate syntax with explicit typed row and outer arrays. Add a test that writes a synthetic private-format header, compiles it against the actual V607 observer header under -Werror, and checks the second lane's flush LR. No guest or owner bytes are used in this test. Owner preparation retry is pending.
