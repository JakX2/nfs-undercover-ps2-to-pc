// Phase 7 research-only deterministic prototype.
// Recreates one observed Undercover PS2/Wii conditional branch.
// Does NOT hook the game, use game memory offsets, or replicate RNG implementation.
#include <cassert>
#include <cstdio>

// This is the observed comparison's effect on a manager flag, abstracted.
// The identity/meaning of the flag remains an inference from call context.
static bool apply_probability_gate(bool manager_flag, float probability, float random_0_to_1) {
    if (manager_flag && random_0_to_1 > probability) {
        manager_flag = false;
    }
    return manager_flag;
}

int main() {
    assert(apply_probability_gate(true, 0.25f, 0.50f) == false);
    assert(apply_probability_gate(true, 0.75f, 0.50f) == true);
    assert(apply_probability_gate(true, 0.50f, 0.50f) == true); // strictly greater, not >=
    assert(apply_probability_gate(false, 0.75f, 0.50f) == false);
    assert(apply_probability_gate(true, 1.00f, 0.50f) == true);
    std::puts("All five deterministic pursuit-gate branch tests passed.");
}
