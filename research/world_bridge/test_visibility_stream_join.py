"""Synthetic-only tests: visibility↔stream↔scenery cross-reference controls."""
import unittest
from visibility_stream_join import coverage, compare_drivable, is_subsequence, compare_stream_inventory


def row(refs, capacity=None, most=None):
    return {'refs': tuple(refs), 'capacity': len(refs) if capacity is None else capacity,
            'most': len(refs) if most is None else most}


class VisibilityStreamJoinTests(unittest.TestCase):
    def test_known_ids_join(self):
        result = coverage({1: b'', 2: b''}, {1: 4}, {1: row((1,2))}, (2,))
        self.assertEqual((result['visibility_unique_targets_in_stream_rows'],
                          result['scene_roots_in_visibility_targets']), (2,1))

    def test_scene_not_in_target_is_not_error(self):
        result = coverage({1: b'', 2600: b''}, {1: 4}, {1: row((1,))}, (2600,))
        self.assertEqual(result['scene_roots_not_in_visibility_targets'], 1)

    def test_reject_scene_missing_stream_row(self):
        with self.assertRaisesRegex(ValueError, 'no parent streaming row'):
            coverage({1: b''}, {}, {1:row((1,))}, (999,))

    def test_accept_positive_unresolved_target(self):
        result = coverage({1: b''}, {}, {1: row((32767,))})
        self.assertEqual(result['visibility_unique_targets_outside_stream_rows'], 1)

    def test_reject_zero_target(self):
        with self.assertRaisesRegex(ValueError, 'Invalid visibility target'):
            coverage({1: b''}, {}, {1: row((0,))})

    def test_reject_negative_target(self):
        with self.assertRaisesRegex(ValueError, 'Invalid visibility target'):
            coverage({1: b''}, {}, {1: row((-1,))})

    def test_reference_count_including_duplicate_across_rows(self):
        result = coverage({1: b''}, {}, {1: row((5,)), 2: row((5,))})
        self.assertEqual(result['visibility_reference_occurrences'], 2)
        self.assertEqual(result['visibility_unique_targets'], 1)

    def test_subsequence_with_two_insertions(self):
        self.assertTrue(is_subsequence((1, 3, 5), (1, 2, 3, 4, 5)))

    def test_subsequence_rejects_reorder(self):
        self.assertFalse(is_subsequence((1, 3, 2), (1, 2, 3)))

    def test_subsequence_empty(self):
        self.assertTrue(is_subsequence((), (1, 2)))

    def test_subsequence_rejects_duplicate_missing(self):
        self.assertFalse(is_subsequence((1, 1), (1,)))

    def test_only_additions_do_not_change_target_universe(self):
        left = {1: row((1, 2, 3), 5, 3), 2: row((2, 3))}
        right = {1: row((1, 3), 4, 2), 2: row((2, 3))}
        result = compare_drivable(left, right)
        self.assertEqual(result['different_row_count'], 1)
        self.assertEqual(result['changed_rows_with_left_only_order_preserving_insertions'], 1)
        self.assertTrue(result['same_global_target_id_set'])

    def test_removed_reference_breaks_insertion_check(self):
        left = {1: row((1, 4), 3, 2)}
        right = {1: row((1, 3), 2, 2)}
        result = compare_drivable(left, right)
        self.assertEqual(result['changed_rows_with_left_only_order_preserving_insertions'], 0)
        self.assertEqual(result['left_only_reference_occurrences_in_changed_rows'], 1)
        self.assertEqual(result['right_only_reference_occurrences_in_changed_rows'], 1)

    def test_same_refs_but_different_capacity_not_added(self):
        left = {1: row((1, 2), 4, 2)}
        right = {1: row((1, 2), 3, 2)}
        result = compare_drivable(left, right)
        self.assertEqual(result['different_row_count'], 1)
        self.assertEqual(result['changed_rows_with_left_only_order_preserving_insertions'], 0)

    def test_no_common_rows(self):
        result = compare_drivable({1: row((1,))}, {2: row((2,))})
        self.assertEqual((result['shared_drivable_section_ids'], result['rows_only_left'],
                          result['rows_only_right']), (0,1,1))

    def test_comparison_truncates_large_id_list(self):
        a = {i: row((i, i+100)) for i in range(1, 40)}
        b = {i: row((i,)) for i in range(1, 40)}
        result = compare_drivable(a,b)
        self.assertTrue(result['different_row_id_list_truncated'])
        self.assertEqual(len(result['different_row_ids']), 32)

    def test_extra_stream_rows_are_covered_by_existing_visibility(self):
        left = {1: b'', 2: b'', 3: b''}
        right = {1: b''}
        drivable = {10: row((1,2,3))}
        result = compare_stream_inventory(left, right, drivable, drivable)
        self.assertEqual(result['only_left_stream_ids'], 2)
        self.assertEqual(result['left_only_stream_ids_in_left_visibility_targets'], 2)
        self.assertTrue(result['same_global_visibility_target_id_set'])

    def test_extra_stream_rows_unreferenced_remain_allowed(self):
        result = compare_stream_inventory({1:b'', 2:b''}, {1:b''},
                                          {10:row((1,))}, {10:row((1,))})
        self.assertEqual(result['left_only_stream_ids_in_left_visibility_targets'], 0)

    def test_stream_comparator_nonidentical_target_universe(self):
        result = compare_stream_inventory({1:b''}, {1:b''},
                                          {10:row((1,))}, {10:row((2,))})
        self.assertFalse(result['same_global_visibility_target_id_set'])

    def test_empty_sets(self):
        result = coverage({}, {}, {})
        self.assertEqual((result['stream_rows'], result['visibility_unique_targets']), (0,0))


if __name__ == '__main__':
    unittest.main()
