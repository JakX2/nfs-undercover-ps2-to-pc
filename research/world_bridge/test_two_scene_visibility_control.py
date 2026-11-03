"""Synthetic-only regression tests for joined Carbon PC/PS2 controls."""
import unittest
from two_scene_visibility_control import select_controls, visible_targets
from test_scenery_model_hash_bridge import instances, record
from scenery_model_hash_bridge import promote_model_hash0


def test_scenes(ids=(141,142), pc=True):
    result = {}
    for i in ids:
        source_info = record(h1=i) + record(h1=i+1000)
        result[i] = {'children': {
            0x34103: instances(0,1),
            0x34105: b'tree' + bytes([i % 128]),
            0x34102: promote_model_hash0(source_info) if pc else source_info,
        }}
    return result


def check(pc=None, ps2=None, pc_ids=(141,142), ps2_ids=(141,142),
          pc_targets=(141,142), ps2_targets=(141,142), count=2):
    return select_controls(
        test_scenes() if pc is None else pc,
        test_scenes(pc=False) if ps2 is None else ps2,
        {i: None for i in pc_ids}, {i:None for i in ps2_ids},
        set(pc_targets), set(ps2_targets), count)


class TwoSceneControlTests(unittest.TestCase):
    def test_two_independent_controls(self):
        r = check()
        self.assertEqual(r['qualifying_controls'], 2)
        self.assertEqual([x['section_id'] for x in r['selected_controls']], [141,142])
        self.assertEqual((r['total_selected_instances'],r['total_selected_info_records']), (4,4))

    def test_requires_two(self):
        with self.assertRaisesRegex(ValueError,'Fewer than two'):
            check(pc_targets=(141,))

    def test_requires_stream_on_both_platforms(self):
        with self.assertRaisesRegex(ValueError,'Fewer than two'):
            check(ps2_ids=(142,))

    def test_requires_visibility_on_both_platforms(self):
        with self.assertRaisesRegex(ValueError,'Fewer than two'):
            check(ps2_targets=(142,))

    def test_rejects_nonidentical_tree(self):
        ps2 = test_scenes(pc=False)
        ps2[142]['children'][0x34105]=b'changed'
        with self.assertRaisesRegex(ValueError,'Fewer than two'):
            check(ps2=ps2)

    def test_rejects_nonidentical_instance(self):
        ps2 = test_scenes(pc=False)
        ps2[142]['children'][0x34103]=instances(1,0)
        with self.assertRaisesRegex(ValueError,'Fewer than two'):
            check(ps2=ps2)

    def test_rejects_unexpected_pc_info_change(self):
        pc = test_scenes()
        p = bytearray(pc[142]['children'][0x34102]);p[50]=0x99
        pc[142]['children'][0x34102]=bytes(p)
        with self.assertRaisesRegex(ValueError,'differs beyond'):
            check(pc=pc)

    def test_detects_invalid_info_index(self):
        pc = test_scenes()
        ps2 = test_scenes(pc=False)
        pc[142]['children'][0x34103]=instances(0,2)
        ps2[142]['children'][0x34103]=instances(0,2)
        with self.assertRaisesRegex(ValueError,'invalid info index'):
            check(pc=pc,ps2=ps2)

    def test_excludes_special_z0(self):
        pc=test_scenes((141,142,2600));ps2=test_scenes((141,142,2600),pc=False)
        r=check(pc=pc,ps2=ps2,pc_ids=(141,142,2600),ps2_ids=(141,142,2600),
                pc_targets=(141,142,2600),ps2_targets=(141,142,2600))
        self.assertEqual(r['qualifying_controls'],2)

    def test_choose_at_least_two_controls(self):
        with self.assertRaisesRegex(ValueError,'between two'):
            check(count=1)

    def test_more_requested_than_qualifying(self):
        with self.assertRaisesRegex(ValueError,'Fewer than two'):
            check(count=3)

    def test_empty_visibility_target_set(self):
        self.assertEqual(visible_targets({}),set())
        self.assertEqual(visible_targets({1:{'refs':(2,3)},2:{'refs':(3,)}}),{2,3})


if __name__=='__main__': unittest.main()
