# V57: iterative candidate Wii scenery tree auditor

**Source-only, read-only tooling. No new original game fixtures and no Carbon PC runtime proof.**

## Issue fixed

V56's candidate `0x34105` tree auditor recursively descended a hypothetical
48-byte-node graph and collected *all descendant instance rows* at each
ancestor. A chain of more than ~1,000 nodes could crash with Python's
`RecursionError`. Repeatedly extending descendant lists also wastes memory
for deep hierarchies.

V57 changes only this traversal. It **does not** assert that such deep trees
occur in the original Wii game.

## Behavior

The replacement traversal uses an explicit enter/exit DFS stack and a
post-order AABB union for each node. It preserves the existing V56 candidate
format and rejects:

- child indices outside the node array;
- cycles and children reached through more than one parent;
- missing or repeated instance references;
- unreachable graph nodes and empty nodes;
- invalid or non-finite AABBs and node unions differing beyond the supplied
  tolerance.

Each node stores only an aggregate minimum/maximum box, not the complete
descendant list. The traversal's memory/time for these operations is linear in
the nodes and references, apart from reading and validating each input row.

## Testing and provenance

The V56 26 asset-free cases are retained. Six new synthetic cases cover a
1,500-node tree, a 1,200-node cycle, repeated leaf indices, unreachable nodes,
out-of-range children and a valid branched tree. The original Wii fixture
tests remain conditional on the user's local `NFS_UC_WII_SCENE` and are not
shipped or run on public CI.

Run:

```sh
python -m unittest discover -s research/v56 -p 'test_v56.py' -v
```

**Important:** A structurally consistent candidate graph still proves neither
visibility semantics nor Carbon PC disk ABI, loader behavior, streaming,
collision, shader materials, navigation or an installable mod. The project
still needs another independently authenticated original Wii scenery ROOT and
an authenticated Carbon PC world scene.
