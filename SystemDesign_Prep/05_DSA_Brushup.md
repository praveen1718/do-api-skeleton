# DSA Brush-Up — What Actually Comes Up on This Interview Day

**Expectation-setting:** your hiring day has no dedicated DSA round. Where data structures CAN appear: (1) inside the build ("why a dict here?", dedupe/aggregation logic), (2) the Architecture Review ("what's the complexity of your processing step? what happens at 10M records?"), (3) the design round (choosing structures for indexes/queues). DO's *earlier* screening rounds have used LeetCode-style questions (graphs, strings, arrays — see prep doc 02 sources), so a light refresh is cheap insurance. This doc is that refresh — 30 minutes, not a grind.

## 1. Complexity you should say without thinking

| Structure (Python) | Op | Cost | One-liner you might say in review |
|---|---|---|---|
| `dict` / `set` (hash table) | get/put/in | O(1) avg | "Dedupe by ID is a set lookup — O(1) per record, O(n) for the batch." |
| `list` (dynamic array) | append / index | O(1) am. / O(1) | "Append-only event buffer." |
| `list` | insert(0,·) / `x in list` | O(n) | why you DON'T scan lists for membership |
| `collections.deque` | popleft/append | O(1) | in-memory FIFO queue, sliding windows |
| `heapq` (binary heap) | push/pop | O(log n) | top-K, scheduling next-due job, rate-limiter timers |
| Sorted array / `bisect` | search | O(log n) | percentiles over a static batch |
| B-tree (DB index) | search/insert | O(log n) | "every WHERE/ORDER BY column I query is B-tree indexed" |
| Balanced BST / skiplist | ordered ops | O(log n) | Redis sorted sets (leaderboards, sliding-window rate limits) |

Sorting: O(n log n) (Timsort). Hashing a batch: O(n). String concat in a loop: O(n²) — use `''.join`.

## 2. The five structures behind system-design components (be able to name these)

1. **Hash map** → caches, dedupe, session stores, shard routing (consistent hashing = hash ring).
2. **Heap / priority queue** → top-K trending, task schedulers, timer wheels, Dijkstra-ish nearest.
3. **Log / append-only array** → Kafka partitions, WALs, LSM memtables. Sequential I/O is why writes are fast.
4. **B-tree vs LSM-tree** → B-tree: read-optimized, in-place (Postgres). LSM: write-optimized, compaction (Cassandra, RocksDB). One sentence each is staff-level signal.
5. **Graph + adjacency sets** → the DO package-dependency question: `deps: dict[str, set]` + reverse index `rdeps: dict[str, set]`; cycle check = DFS with visiting/visited states; "what breaks if I remove X" = BFS over rdeps (transitive closure).

Bonus one-liners: **Bloom filter** ("cheap probabilistic 'definitely not present' — saves disk lookups"), **HyperLogLog** ("approximate distinct counts in KBs"), **inverted index** ("word → doc list; how Elasticsearch works"), **geohash/quadtree** ("2D → sortable 1D for proximity").

## 3. Patterns likely inside a 3-hour ingestion build

- **Dedupe:** `seen: set[str]`; idempotency = same input, same result, no double effects.
- **Aggregation:** single pass with `dict[key, (count, sum, min, max)]` — O(n), constant memory per key. Percentiles: sort the batch O(n log n) or keep a heap.
- **Top-K:** `heapq.nlargest(k, items)` — O(n log k), never sort everything for K items.
- **Sliding window (rate limit / rolling stats):** deque of timestamps, evict from left.
- **Streaming a big file:** iterate line-by-line (O(1) memory), never `read()` a 2GB upload; batch DB writes every N records.
- **Graph/deps input:** build forward + reverse adjacency immediately; most questions become trivial traversals.

## 4. If a screen-style question sneaks in (their reported favorites)

Reported DO coding themes (AlgoDaily/Glassdoor): graph-is-a-tree (n-1 edges + connected + no cycle), duplicate words / frequency maps, substring search, contiguous subarray sum (prefix sums / Kadane), edit distance (2D DP), max rectangle in histogram (monotonic stack). If you have 45 spare minutes ever: re-solve *graph-is-a-tree* and *subarray sum* — the other patterns follow.

## 5. Review-proofing your build (say complexity before they ask)

For each endpoint be ready with one sentence: "POST /ingest is O(n) in batch size with O(u) memory for u unique IDs; GET /results is O(k) over aggregated keys; at 10M records/day none of this is the bottleneck — the network and the datastore are, which is why I'd add a queue before workers rather than optimize this loop."
