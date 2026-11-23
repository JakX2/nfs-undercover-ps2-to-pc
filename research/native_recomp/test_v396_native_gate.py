#!/usr/bin/env python3
"""V396 owner-result gate synthetic tests; no proprietary source required."""
from pathlib import Path
import tempfile
import unittest
from audit_v396_native_gate import verify

ENTRY395 = (
    "V395_NAND_ISFS_NEXT guest=1 clear=1 masked=1 registered=1 "
    "mapped=1 selected=1 userdata=1 nand=0\n"
)
ENTRY396 = (
    "V396_NAND_CB_BODY kind=2 verified=1 owned=0 clear=1 "
    "masked=0 registered=1 cache=0 context=0 nand=0 bounded=1\n"
)
T392 = "V392_NAND_POST_CACHE_TRIAL kind=1 stopped=1 completed=1\n"
T393 = "V393_NAND_NEXT_TRIAL first=1 next=1 completed=1\n"
T394 = "V394_NAND_ISFS_TRIAL context=1 isfs=1 completed=1\n"
T395 = "V395_NAND_ISFS_TRIAL isfs=1 next=1 completed=1\n"
T396 = "V396_NAND_CB_TRIAL kind=2 stopped=1 completed=1\n"
EVENT = ENTRY395 + ENTRY396 + T392 + T393 + T394 + T395 + T396

def run(raw: str, rc: int = 0) -> bool:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "owner-private.log"
        path.write_text(raw, encoding="ascii")
        return verify(path, rc)

class Tests(unittest.TestCase):
    def test_sixteen_realistic_bounded_pairs_and_clean_exit(self):
        self.assertTrue(run(EVENT * 16))
        self.assertFalse(run(EVENT * 16, 134))
        self.assertFalse(run(EVENT * 16, 124))
        self.assertFalse(run(EVENT * 16, 1))

    def test_incomplete_or_false_positive_chains_fail_closed(self):
        for raw in (
            "", EVENT, EVENT * 15, EVENT * 17,
            (EVENT * 15) + ENTRY395 + ENTRY396 + T392 + T393 + T394 + T395,
            (EVENT * 15) + EVENT.replace("selected=1", "selected=0"),
            (EVENT * 15) + EVENT.replace("userdata=1", "userdata=0"),
            (EVENT * 15) + EVENT.replace("completed=1", "completed=0", 1),
            (EVENT * 15) + EVENT.replace("verified=1", "verified=0"),
            (EVENT * 15) + EVENT.replace("bounded=1", "bounded=0"),
            (EVENT * 15) + EVENT.replace(T396, T396 + T396),
            (EVENT * 15) + "PRIVATE STATE\n" + ENTRY395,
        ):
            with self.subTest(case=len(raw)):
                self.assertFalse(run(raw))

    def test_post_entry_hardware_state_is_diagnostic(self):
        changed = ENTRY396.replace("clear=1", "clear=0").replace(
            "registered=1", "registered=0")
        self.assertTrue(run((ENTRY395 + changed +
                             T392 + T393 + T394 + T395 + T396) * 16))

    def test_no_raw_log_exposed_by_gate(self):
        raw = ("private address 0xCAFEBABE\n" + EVENT) * 16
        self.assertTrue(run(raw))

if __name__ == "__main__":
    unittest.main()
