"""Synthetic-only tests for paired Z0 scenery and visibility frame boundaries."""
import struct
import unittest
from scenery_visibility_anchor import (frame_children, find_unique_chunk,
                                       locate_z0_row, inspect_one, SCENE_CHILDREN,
                                       SCENE_ROOT, VISIBILITY_CHILDREN,
                                       VISIBILITY_ROOT, STREAM_INDEX)
from test_section_identity_anchor import row


def frame(root, *children):
    data = b''.join(struct.pack('<II', cid, len(content)) + content for cid, content in children)
    return struct.pack('<II', root, len(data)) + data


def bun_and_stream():
    scene = frame(SCENE_ROOT, *((cid, b'hello') for cid in SCENE_CHILDREN))
    vis = frame(VISIBILITY_ROOT, *((cid, b'') for cid in VISIBILITY_CHILDREN))
    ix = struct.pack('<II', STREAM_INDEX, 92) + row(name=b'Z0', section=2600, offset=0, size=4096)
    return vis + ix, scene + bytes(4096)


class SceneryVisibilityAnchorTests(unittest.TestCase):
    def test_scene_children(self):
        root = frame(SCENE_ROOT, *((cid, b'1234') for cid in SCENE_CHILDREN))
        got = frame_children(root, SCENE_ROOT, SCENE_CHILDREN)
        self.assertEqual(len(got['child_payload_bytes']), 6)
        self.assertEqual(list(got['child_payload_bytes'].values()), [4] * 6)

    def test_visibility_allows_empty_children(self):
        root = frame(VISIBILITY_ROOT, *((cid, b'') for cid in VISIBILITY_CHILDREN))
        got = frame_children(root, VISIBILITY_ROOT, VISIBILITY_CHILDREN)
        self.assertTrue(got['complete'])

    def test_truncated_header(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            frame_children(b'ABC', SCENE_ROOT, SCENE_CHILDREN)

    def test_wrong_root(self):
        with self.assertRaisesRegex(ValueError, 'expected root'):
            frame_children(frame(3, *((cid, b'') for cid in SCENE_CHILDREN)),
                           SCENE_ROOT, SCENE_CHILDREN)

    def test_unbounded_root(self):
        x = bytearray(frame(SCENE_ROOT, *((cid, b'') for cid in SCENE_CHILDREN)))
        struct.pack_into('<I', x, 4, 999999)
        with self.assertRaisesRegex(ValueError, 'out-of-bounds'):
            frame_children(bytes(x), SCENE_ROOT, SCENE_CHILDREN)

    def test_child_out_of_bounds(self):
        x = bytearray(frame(SCENE_ROOT, *((cid, b'') for cid in SCENE_CHILDREN)))
        struct.pack_into('<I', x, 12, 8888)
        with self.assertRaisesRegex(ValueError, 'overruns'):
            frame_children(bytes(x), SCENE_ROOT, SCENE_CHILDREN)

    def test_child_wrong_order(self):
        children = list(SCENE_CHILDREN)
        children[0], children[1] = children[1], children[0]
        with self.assertRaisesRegex(ValueError, 'order'):
            frame_children(frame(SCENE_ROOT, *((cid, b'') for cid in children)),
                           SCENE_ROOT, SCENE_CHILDREN)

    def test_full_synthetic_pair(self):
        bun, stream = bun_and_stream()
        report = inspect_one(bun, stream, len(stream))
        self.assertTrue(report['z0_scene_frame_within_section'])
        self.assertEqual(report['z0_scene_root']['child_payload_bytes']['0x00034101'], 5)

    def test_duplicate_top_chunk(self):
        bun, _ = bun_and_stream()
        chunk = find_unique_chunk(bun, VISIBILITY_ROOT)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            find_unique_chunk(bun + chunk, VISIBILITY_ROOT)

    def test_missing_chunk(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            find_unique_chunk(b'', VISIBILITY_ROOT)

    def test_top_chunk_truncation(self):
        with self.assertRaisesRegex(ValueError, 'out of bounds'):
            find_unique_chunk(struct.pack('<II', VISIBILITY_ROOT, 999), VISIBILITY_ROOT)

    def test_missing_z0(self):
        idx = struct.pack('<II', STREAM_INDEX, 92) + row(name=b'A0', section=100)
        with self.assertRaisesRegex(ValueError, 'Missing Z0'):
            locate_z0_row(idx, 10000)

    def test_wrong_z0_name(self):
        idx = struct.pack('<II', STREAM_INDEX, 92) + row(name=b'A0', section=2600)
        with self.assertRaisesRegex(ValueError, 'Unexpected section'):
            locate_z0_row(idx, 10000)

    def test_z0_stream_root_absent(self):
        bun, stream = bun_and_stream()
        with self.assertRaisesRegex(ValueError, 'does not start'):
            inspect_one(bun, b'xxxx' + stream[4:], len(stream))

    def test_z0_section_too_short(self):
        bun, stream = bun_and_stream()
        raw = bytearray(bun)
        pos = raw.find(b'Z0')
        struct.pack_into('<I', raw, pos + 0x18, 16)
        struct.pack_into('<I', raw, pos + 0x1c, 16)
        with self.assertRaisesRegex(ValueError, 'overflows'):
            inspect_one(bytes(raw), stream, len(stream))


if __name__ == '__main__':
    unittest.main()
